#include <boost/asio.hpp>
#include <boost/asio/awaitable.hpp>
#include <boost/asio/co_spawn.hpp>
#include <boost/asio/detached.hpp>
#include <boost/asio/use_awaitable.hpp>
#include <boost/beast/http/field.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast.hpp>
#include <memory>
#include <nlohmann/json.hpp>
#include <optional>

#include "apollo/CDPConnection.h"
#include "apollo/Logger.hpp"
#include "apollo/IScript.h"
#include "apollo/Browser.h"

using boost::asio::awaitable;
using boost::asio::co_spawn;
using boost::asio::detached;
namespace ws = boost::beast::websocket;
namespace beast = boost::beast;
namespace http = beast::http;
namespace asio = boost::asio;
using json = nlohmann::json;
using tcp = asio::ip::tcp;



class TestScript : public apl::IScript
{
public:
  awaitable<int> exec(apl::CDPConnection& conn, const std::string& sessionId) override
  {
    auto resp = co_await conn.send_command("Page.navigate", {{"url", "http://example.com"}}, sessionId);
    INFO("Script response = %s\n", resp.dump(2).c_str());
    co_return 0;
  }
};

int main() {
  std::unique_ptr<TestScript> testScript = std::make_unique<TestScript>();
  apl::Browser browser("127.0.0.1", "9222");
  browser.addScript(std::move(testScript));
  browser.run();
  return 0;
}

