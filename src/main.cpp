#include <boost/asio.hpp>
#include <boost/asio/awaitable.hpp>
#include <boost/asio/use_awaitable.hpp>
#include <boost/beast/http/field.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast.hpp>
#include <nlohmann/json.hpp>
#include <optional>

#include "apollo/Logger.hpp"

using boost::asio::awaitable;
using boost::asio::co_spawn;
using boost::asio::detached;
namespace ws = boost::beast::websocket;
namespace beast = boost::beast;
namespace http = beast::http;
namespace asio = boost::asio;
using json = nlohmann::json;
using tcp = asio::ip::tcp;

struct UrlParts {
    std::string scheme;
    std::string host;
    std::string port;
    std::string path;
};

UrlParts parse_url(const std::string& url) {
    UrlParts parts;

    auto scheme_end = url.find("://");
    if (scheme_end == std::string::npos)
        throw std::runtime_error("Invalid URL, missing scheme");

    parts.scheme = url.substr(0, scheme_end);

    auto host_start = scheme_end + 3;
    auto path_start = url.find('/', host_start);

    if (path_start == std::string::npos) {
        parts.host = url.substr(host_start);
        parts.path = "/";
    } else {
        parts.host = url.substr(host_start, path_start - host_start);
        parts.path = url.substr(path_start);
    }

    // Split host and port if present
    auto colon_pos = parts.host.find(':');
    if (colon_pos != std::string::npos) {
        parts.port = parts.host.substr(colon_pos + 1);
        parts.host = parts.host.substr(0, colon_pos);
    } else {
        // default port
        if (parts.scheme == "ws")
            parts.port = "80";
        else if (parts.scheme == "wss")
            parts.port = "443";
        else
            parts.port = "80";
    }

    return parts;
}

// Async write helper
awaitable<void> async_send(ws::stream<tcp::socket>& socket, const json& msg) {
    co_await socket.async_write(
        asio::buffer(msg.dump()), asio::use_awaitable);
}

// Async read helper
awaitable<json> async_read(ws::stream<tcp::socket>& socket) {
    boost::beast::flat_buffer buffer;
    co_await socket.async_read(buffer, asio::use_awaitable);
    std::string s((char*)buffer.data().data(), buffer.size());
    co_return json::parse(s);
}

awaitable<std::optional<ws::stream<tcp::socket>>> connect_cdp(asio::io_context& ioc, const std::string& url) {
    tcp::resolver resolver(ioc);
    try {
      auto urlParts = parse_url(url);
      auto endpoints = co_await resolver.async_resolve(urlParts.host, urlParts.port, asio::use_awaitable);

      ws::stream<tcp::socket> ws_socket(ioc);
      co_await asio::async_connect(ws_socket.next_layer(), endpoints, asio::use_awaitable);
      co_await ws_socket.async_handshake("localhost", urlParts.path, asio::use_awaitable);
      co_return ws_socket;
    } catch (const boost::system::system_error& e) {
      ERROR("Failed to connect\n");
      co_return std::nullopt;
    } catch (const std::exception& e) {
      ERROR("Other error\n");
      co_return std::nullopt;
    }

}

awaitable<std::optional<std::string>> get_cdp_ws_url(asio::io_context& ioc) {
    try {
      tcp::resolver resolver(ioc);
      auto endpoints = co_await resolver.async_resolve("127.0.0.1", "9222", asio::use_awaitable);

      beast::tcp_stream stream(ioc);
      co_await stream.async_connect(endpoints, asio::use_awaitable);

      // HTTP GET /json
      http::request<http::string_body> req{http::verb::get, "/json", 11};
      req.set(http::field::host, "127.0.0.1:9222");
      req.set(http::field::user_agent, "C++ CDP Client");

      co_await http::async_write(stream, req, asio::use_awaitable);

      beast::flat_buffer buffer;
      http::response<http::string_body> res;
      co_await http::async_read(stream, buffer, res, asio::use_awaitable);

      // Parse JSON
      auto pages = json::parse(res.body());
      if(pages.empty()) {
        co_return std::nullopt;
      }
      INFO("Pages: %s\n", pages.dump().c_str());

      std::string ws_url = pages[0]["webSocketDebuggerUrl"];
      co_return ws_url;
    } catch (const std::exception& e) {
      ERROR("Failed to get CDP ws url: \n", e.what());
      co_return std::nullopt;
    }
}

awaitable<json> send_command(ws::stream<tcp::socket>& ws, int id, const std::string& method, const json& params) {
    json msg = {{"id", id}, {"method", method}, {"params", params}};
    co_await async_send(ws, msg);

    for (;;) {
        json resp = co_await async_read(ws);
        if (resp.contains("id") && resp["id"] == id) {
            co_return resp;
        } else if (resp.contains("method")) {
            // handle events asynchronously
            INFO("Event: %s\n", resp.dump().c_str());
        }
    }
}

int main() {
    asio::io_context ioc;

    co_spawn(ioc, [&]() -> awaitable<void> {
        auto url_opt = co_await get_cdp_ws_url(ioc);
        if(!url_opt) {
          ERROR("Url is null\n");
          co_return;
        }
        auto& url = *url_opt;
        INFO("Url for CDP connect: %s\n", url.c_str());
        auto ws_opt = co_await connect_cdp(ioc, url);
        if(!ws_opt) {
          ERROR("WebSocket is null\n");
          co_return;
        }
        auto& ws = *ws_opt;
        json nav = co_await send_command(ws, 1, "Page.navigate", {{"url", "https://example.com"}});
        INFO("Navigation response: %s\n", nav.dump().c_str());
    }, detached);

    ioc.run();
    return 0;
}

