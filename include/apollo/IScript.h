#ifndef ISCRIPT_H
#define ISCRIPT_H

#include "apollo/CDPConnection.h"
#include <boost/asio/use_awaitable.hpp>

using boost::asio::awaitable;

namespace apl
{

class IScript
{
public:
  virtual awaitable<int> exec(CDPConnection& conn, const std::string& sessionId) = 0;
  virtual ~IScript() = default;
};

} // namespace apl

#endif // ISCRIPT_H
