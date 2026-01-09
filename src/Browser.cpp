#include "apollo/Browser.h"

namespace apl
{

awaitable<int> Browser::connect()
{
  try {
    tcp::resolver resolver(mIoc);
    auto endpoints = co_await resolver.async_resolve(mHost, mPort, asio::use_awaitable);

    beast::tcp_stream stream(mIoc);
    co_await stream.async_connect(endpoints, asio::use_awaitable);

    http::request<http::string_body> req{http::verb::get, "/json/version", 11};
    req.set(http::field::host, mHost + ":" + mPort);
    req.set(http::field::user_agent, "C++ CDP Client");

    co_await http::async_write(stream, req, asio::use_awaitable);

    beast::flat_buffer buffer;
    http::response<http::string_body> res;
    co_await http::async_read(stream, buffer, res, asio::use_awaitable);

    INFO("/json/version raw response: %s\n", res.body().c_str());
    auto resp = json::parse(res.body());
    // TODO: extract browser info (version, agent, v8-version and so on

    std::string wsUrl = resp["webSocketDebuggerUrl"];
    auto ret = co_await mCDPConn.connect(wsUrl);
    co_return ret;
  } catch (const std::exception& e) {
    ERROR("Failed to get CDP ws url: %s\n", e.what());
    co_return 1;
  }
}

int Browser::addScript(std::unique_ptr<IScript>&& script) {
  if(!script) {
    ERROR("Script is nullptr\n");
    return 1;
  }
  IScript* script_raw = script.release();
  co_spawn(mIoc, [script_raw, this]() -> awaitable<int> {
    auto res = co_await connect();
    INFO("Connection result = %d\n", res);
    const std::string method = "Target.createTarget";
    const std::string url = "about:blank";
    json resp = co_await mCDPConn.send_command(method, {{"url", url}});
    INFO("Sending attach target\n");
    const std::string targetId = resp["result"]["targetId"];
    json attachResp = co_await mCDPConn.send_command("Target.attachToTarget", {{"targetId", targetId}, {"flatten", true}});
    // TODO: check for json fields 
    const std::string sessionId = attachResp["result"]["sessionId"];
    INFO("Prepare to execute script for session id: %s\n", sessionId.c_str());
    co_await mCDPConn.send_command(
        "Page.enable",
        {},
        sessionId
    );
    mConns[sessionId] = script_raw;
    auto ret = co_await mConns[sessionId]->exec(mCDPConn, sessionId);
    co_return ret;
  }, detached);
  return 0;
}

void Browser::run()
{
  mIoc.run();
}

} // namespace apl
