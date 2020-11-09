#
# (c) 2020 - AWS.
# Common base for all subsystem makefiles.
#

PWD ?= pwd_unknown
BASE_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

export PROJECT_ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
export SERVICES_DIR := $(BASE_DIR)lib
RUNTIME_CONFIG_FILE ?= $(BASE_DIR)/stackoutput.json


# This parses the input config file.
# Invoke it as:
# export VALUE ?= $(call FromInCfg,configFile,key)
#
define FromInConf
$(shell node -p "require('$(1)').$(2)")
endef

# This parses the output file generated after a CDK stage is run.
# Invoke it as:
# export VALUE ?= $(call FromOutCfg,configFile,stackName,key)
#
define FromOutConf
$(shell node -p "require('$(1)').$(2).$(3)")
endef

