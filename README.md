# apollo

C++ wrapper around CDP

one chromium instace - one instance of apollo

./scripts/prepare_
cmake --preset conan-debug ..


## Run chrome with CDP

## How it should work


one cdp connection have:
- 1 reader coroutine (for read responses and events)
- 1 or more writer coroutine (that will be sending commands)


