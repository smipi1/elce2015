

BIN_DIR=./bin
BUILD_DIR=./build_dir
ONION_BUILD_DIR=${BUILD_DIR}/onion
ONION_SRC_DIR=onion
ONION_SOME_FILE=$(ONION_SRC_DIR)/CMakeLists.txt

all: $(BIN_DIR)/trivia

$(BUILD_DIR) $(ONION_BUILD_DIR) $(BIN_DIR):
	mkdir -p $@

$(ONION_SOME_FILE):
	git submodule init $(dirname $@)
	git submodule update

.PHONY : $(BIN_DIR)/trivia
$(BIN_DIR)/trivia: $(BIN_DIR) $(ONION_BUILD_DIR) $(ONION_SOME_FILE)
	cd $(ONION_BUILD_DIR) && cmake $(abspath $(ONION_SRC_DIR))
	make -C $(ONION_BUILD_DIR)
	cp -a $(ONION_BUILD_DIR)/examples/trivia/trivia $(BIN_DIR)/trivia
