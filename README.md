# apollo

C++ wrapper around CDP

one chromium instace - one instance of apollo

./scripts/prepare_
cmake --preset conan-debug ..


## Run chrome with CDP

## TODO:

- low hardcode for parsing CDP docs into separate codegen folder
- add script by pointer (probably with no memory freeing inside) -> support multiple tabs with same script -> change script param -> next
- events? handling? -> user should be able to react to them (for example: Page.loadEventFired)
    - events are not global, so must read all events (and all responses) and then send them to their tabs
- so we must store coroutines by their sessionId
