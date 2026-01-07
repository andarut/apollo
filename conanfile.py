from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout

class ApolloRecipe(ConanFile):
    name = "apollo"
    version = "0.1"
    settings = "os", "compiler", "build_type", "arch"

    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def build_requirements(self):
        self.tool_requires("cmake/3.23.5")
        self.requires("nlohmann_json/3.12.0")
        self.requires("boost/1.90.0")

    def generate(self):
        tc = CMakeToolchain(self, generator="Unix Makefiles")
        # if self.settings.build_type == "Debug":
        #   tc.variables["CMAKE_C_FLAGS"] = "-fsanitize=address,undefined -fno-omit-frame-pointer"
        #   tc.variables["CMAKE_CXX_FLAGS"] = "-fsanitize=address,undefined -fno-omit-frame-pointer"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def layout(self):
        cmake_layout(self)
