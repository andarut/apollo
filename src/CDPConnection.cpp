#include "apollo/CDPConnection.h"
#include "apollo/Url.h"
#include <boost/asio/use_awaitable.hpp>
#include <optional>

using namespace apl;

std::optional<std::string> CDPConnection::getIdFromWsUrl(const std::string& wsUrl) {
    auto pos = wsUrl.find_last_of('/');
    if (pos == std::string::npos || pos + 1 >= wsUrl.size())
        return std::nullopt;
    return wsUrl.substr(pos + 1);
}


awaitable<int> CDPConnection::connect()
{
  try {
    auto url = parseUrl(mWsUrl);
    auto endpoints = co_await mResolver.async_resolve(url.host, url.port, asio::use_awaitable);
    {
      auto idOpt = getIdFromWsUrl(mWsUrl);
      if(!idOpt) {
        ERROR("Failed to get id from ws url\n");
        co_return 3;
      }
      mId = *idOpt;
      INFO("Connection id: %s\n", mId.c_str());
    }

co_await asio::async_connect(mSocket.next_layer(), endpoints, asio::use_awaitable);
    co_await mSocket.async_handshake("localhost", url.path, asio::use_awaitable);
  } catch (const boost::system::system_error& e) {
    ERROR("Failed to connect\n");
    co_return 1;
  } catch (const std::exception& e) {
    ERROR("Other error\n");
    co_return 2;
  }

  co_return 0;
}

awaitable<std::size_t> CDPConnection::async_send(const json& msg)
{
  std::string payload = msg.dump();
  std::size_t bytesWritten = co_await mSocket.async_write(
      asio::buffer(payload), asio::use_awaitable);
  co_return bytesWritten;
}

awaitable<json> CDPConnection::async_read() {
  boost::beast::flat_buffer buffer;
  co_await mSocket.async_read(buffer, asio::use_awaitable);
  std::string s((char*)buffer.data().data(), buffer.size());
  co_return json::parse(s);
}

awaitable<json> CDPConnection::send_command(const std::string& method, const json& params) {
  std::size_t commandId = mCommandId++;
  json msg = {{"id", commandId}, {"method", method}, {"params", params}};
  co_await async_send(msg);
  json resp = co_await wait_for_response(commandId);
  co_return resp;
}

awaitable<json> CDPConnection::wait_for_response(std::size_t id)
{
  asio::experimental::channel<void, std::string> chan(mIoc, 1);
  mPending[id] = chan;
  auto resp = co_await chan.async_receive(asio::use_awaitable);
  mPending.erase(id);
  co_return json::parse(resp);
}

void CDPConnection::deliver_response(std::size_t id, const json& msg)
{
  auto it = mPending.find(id);
  if(it != mPending.end()) {
    it->second.try_send(msh.dump()); 
  }
}

