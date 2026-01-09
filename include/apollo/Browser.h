#ifndef BROWSER_H
#define BROWSER_H

#include <string>
#include <boost/asio.hpp>

#include "apollo/CDPConnection.h"
#include "apollo/IScript.h"

namespace asio = boost::asio;

namespace apl
{
// TODO: check is tab is busy with script -> not create tab for new script, but keep N tabs opened and set script to not busy ones
class Browser
{
public:
  Browser(const std::string& host, const std::string& port) : 
    mHost(host),
    mPort(port),
    mCDPConn(mIoc) {
    INFO("Browser contructor\n");
    }; 
  ~Browser()
  {
   for (auto& [k, ptr] : mConns) {
      delete ptr;
    } 
  }
  awaitable<int> connect(); 
  int addScript(std::unique_ptr<IScript>&& script);
  void run();
private:
  // store in raw pointers because libc++ wanted to copy unique_ptr inside
  std::unordered_map<std::string, IScript*> mConns;
  asio::io_context mIoc;
  CDPConnection mCDPConn;
  std::string mHost;
  std::string mPort;
};

} // namespace apl

#endif // BROWSER_H
