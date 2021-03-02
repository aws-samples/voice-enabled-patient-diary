SELF_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
include $(SELF_DIR)base.mk

INPUT_CONFIG_FILE=config.json
INPUT_CONFIG_PATH=$(SELF_DIR)$(INPUT_CONFIG_FILE)

ifneq ("$(wildcard $(INPUT_CONFIG_PATH))","")
  STACK_CONFIG_NAME := $(call FromInConf,$(INPUT_CONFIG_PATH),stack_config_name)
  AWS_PROFILE := $(call FromInConf,$(INPUT_CONFIG_PATH),aws_profile)
  AWS_REGION := $(call FromInConf,$(INPUT_CONFIG_PATH),region)
  STAGE := $(call FromInConf,$(INPUT_CONFIG_PATH),stage)
else
  $(error Missing input config file: $(INPUT_CONFIG_FILE))
endif

STACK_OUTPUT_PATH=$(SELF_DIR)stackoutput.json

target:
	$(info ${HELP_MESSAGE})
	@exit 0


init:  ## initialize CDK environment. Needed only the first time
	@echo "Initializing CDK environment"
	@cdk bootstrap --profile $(AWS_PROFILE)


deploy: ##=> Deploy services
	$(info [*] Deploying backend...)
	$(MAKE) deploy.backend
	$(MAKE) deploy.lex

deploy.backend: ##=> Deploy backend lambda handlers
	@echo "Pushing CDK stack '$(STACK_CONFIG_NAME)' with profile '$(AWS_PROFILE)' to cloud"
	@npm run build
	@cdk deploy $(STACK_CONFIG_NAME) --profile $(AWS_PROFILE) \
		--require-approval never \
		--outputs-file $(STACK_OUTPUT_PATH) \


deploy.lex:
	$(MAKE) deploy.lex.id
	$(MAKE) deploy.lex.med
	$(MAKE) deploy.lex.symptom
	$(MAKE) deploy.lex.confirm

delete: ##=> Delete services
	$(MAKE) delete.backend

delete.backend: ##=> Delete backend services deployed through CDK
	cdk destroy


deploy.lex.confirm:
	$(info [*] Deploy Lex bot to confirm report time during outbound call...)
	$(eval LAMBDA_ENDPOINT ?= $(call FromOutConf,$(STACK_OUTPUT_PATH),$(STACK_CONFIG_NAME), ConfirmReportTimeLexHandlerArn))
	$(info Confirm report time Lex bot lambda: ${LAMBDA_ENDPOINT})

	lex-bot-deploy -s lex-vui/ConfirmTimeToReport_Export.json --lambda-endpoint ${LAMBDA_ENDPOINT} --verbose --alias ${STAGE} --region ${AWS_REGION}


deploy.lex.id: ##=> Deploy identify verification Lex bot
	$(info [*] Deploy identify verification Lex bot...)
	$(eval LAMBDA_ENDPOINT ?= $(call FromOutConf,$(STACK_OUTPUT_PATH),$(STACK_CONFIG_NAME), VerifyIdentityLexHandlerArn))
	$(info Identify verification Lex bot lambda: ${LAMBDA_ENDPOINT})
	lex-bot-deploy -s lex-vui/VerifyIdentity_Export.json --lambda-endpoint ${LAMBDA_ENDPOINT} --verbose --alias ${STAGE} --region ${AWS_REGION}


deploy.lex.med: ##=> Deploy medication diary Lex bot
	$(info [*] Deploy medication diary Lex bot...)
	$(eval LAMBDA_ENDPOINT ?= $(call FromOutConf,$(STACK_OUTPUT_PATH),$(STACK_CONFIG_NAME), MedicationDiaryHandlerArn))
	$(info Medication diary Lex bot lambda: ${LAMBDA_ENDPOINT})

	lex-bot-deploy -s lex-vui/Medication_Export.json --lambda-endpoint ${LAMBDA_ENDPOINT} --verbose --alias ${STAGE} --region ${AWS_REGION}

deploy.lex.symptom: ##=> Deploy symptom Lex bot
	$(info [*] Deploy symptom Lex bot...)
	$(eval LAMBDA_ENDPOINT ?= $(call FromOutConf,$(STACK_OUTPUT_PATH),$(STACK_CONFIG_NAME), GatherSymptomLexHandlerArn))
	$(info Symptom report Lex bot lambda: ${LAMBDA_ENDPOINT})

	lex-bot-deploy -s lex-vui/SymptomReport_Export.json --lambda-endpoint ${LAMBDA_ENDPOINT} --verbose --alias ${STAGE} --region ${AWS_REGION}



test.bots:
	lex-bot-test --test-file tests/integ/test-symptom-bot.yml --alias dev --quiet

define HELP_MESSAGE

	...::: Bootstraps environment with necessary tools  :::...
	$ make init

	...::: Deploy all resources :::...
	$ make deploy

	...::: Delete all deployed resources :::...
	$ make delete
endef


