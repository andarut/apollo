#include <boost/asio.hpp>
#include <boost/asio/awaitable.hpp>
#include <boost/asio/co_spawn.hpp>
#include <boost/asio/detached.hpp>
#include <boost/asio/use_awaitable.hpp>
#include <boost/beast/http/field.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast.hpp>
#include <nlohmann/json.hpp>
#include <optional>

#include "apollo/CDPConnection.h"
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

int main() {
    asio::io_context ioc;

    co_spawn(ioc, [&]() -> awaitable<void> {
      apl::CDPConnection conn(ioc, "ws://127.0.0.1:9222/devtools/browser/179c5e3f-6f1a-418e-a9e5-7a9431bee1d6");
      co_await conn.connect();
    }, detached);
    ioc.run();
    return 0;
}

