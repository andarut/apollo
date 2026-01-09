#ifndef CDP_CONNECTION_H
#define CDP_CONNECTION_H

#include <boost/asio/io_context.hpp>
#include <cstddef>
#include <string>
#include <unordered_map>

#include <boost/asio.hpp>
#include <boost/asio/awaitable.hpp>
#include <boost/asio/use_awaitable.hpp>
#include <boost/beast/http/field.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast.hpp>
#include <boost/asio/experimental/channel.hpp>
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

namespace apl
{

class CDPConnection
{
public:
  CDPConnection(asio::io_context& ioc) : 
      mResolver(ioc.get_executor()),
      mSocket(ioc.get_executor()),
      mCommandId(1),
      mIoc(ioc)
  {
    INFO("CDP Connection constructor\n");
  }
  awaitable<int> connect(const std::string& wsUrl);
  awaitable<json> send_command(const std::string& method, const json& params, const std::string& sessionId="");
private:
  awaitable<json> wait_for_response(std::size_t id);
  awaitable<std::size_t> async_send(const json& msg);
  awaitable<json> async_read();
  std::optional<std::string> getIdFromWsUrl(const std::string& wsUrl);
private:
  asio::io_context& mIoc;
  // TODO: maybe there is a way to store corouties
  //std::unordered_map<std::size_t, std::function<void(const json&)>> mPending;
  //std::unordered_map<std::size_t, std::shared_ptr<std::promise<json>>> mPending; // map of request id : coroutine that waits its data
  tcp::resolver mResolver; // TODO: store endpoints instead
  ws::stream<tcp::socket> mSocket;
  std::size_t mCommandId;
  std::string mId; // id of page 
  std::string mTitle;
  std::string mUrl;
  std::string mWsUrl;
};

} // namespace apl

#endif // CDP_CONNECTION_H
