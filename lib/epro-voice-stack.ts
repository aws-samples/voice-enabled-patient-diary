import * as cdk from '@aws-cdk/core';
import * as lambda from '@aws-cdk/aws-lambda';
import * as dynamodb from '@aws-cdk/aws-dynamodb';
const iam = require('@aws-cdk/aws-iam');

import {DynamodbBase} from "./defaults/dynamodb-base";
import {LambdaBase} from "./defaults/lambda-base";
import {Common} from './common';
import {Seeder} from 'aws-cdk-dynamodb-seeder';

export class EproVoiceStack extends cdk.Stack {
    constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        let SharedTables: dynamodb.Table[] = [];
        const MedicationDiaryTable = new DynamodbBase(this, 'MedicationDiary', {
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Time_Reported', type: dynamodb.AttributeType.STRING},
        });

        MedicationDiaryTable.addGlobalSecondaryIndex({
            indexName: 'Patient_taken',
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Time_Reported', type: dynamodb.AttributeType.STRING}
        });

        const SymptomTable = new DynamodbBase(this, 'Symptoms', {
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Time_Reported', type: dynamodb.AttributeType.STRING},
        });

        const SurveyCompletionTable = new DynamodbBase(this, 'SurveyCompletion', {
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Report_Date', type: dynamodb.AttributeType.STRING},
        })
        SharedTables.push(SurveyCompletionTable)

        const TrialConfigTable = new DynamodbBase(this, 'TrialConfig', {
            partitionKey: {name: 'Trial_ID', type: dynamodb.AttributeType.STRING}
        })

        new Seeder(this, "TrialConfigSeeder", {
            table: TrialConfigTable,
            setup: require("./ddb-seed/trial-config-setup.json"),
            teardown: require("./ddb-seed/trial-config-teardown.json"),
            refreshOnUpdate: true  // runs setup and teardown on every update, default false
        });

        const PatientProfileTable = new DynamodbBase(this, 'PatientProfile', {
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING}
        })
        SharedTables.push(PatientProfileTable)

        new Seeder(this, "PatientProfileSeeder", {
            table: PatientProfileTable,
            setup: require("./ddb-seed/patient-profile-setup.json"),
            teardown: require("./ddb-seed/patient-profile-teardown.json"),
            refreshOnUpdate: true  // runs setup and teardown on every update, default false
        });

        PatientProfileTable.addGlobalSecondaryIndex({
            indexName: 'Patient_by_Phone',
            partitionKey: {name: 'Phone_Num', type: dynamodb.AttributeType.STRING}
        });

        const EnvVariables = {
            PROFILE_TABLE: PatientProfileTable.tableName,
            SURVEY_COMPLETION_TABLE: SurveyCompletionTable.tableName,
            TRIAL_CONFIG_TABLE: TrialConfigTable.tableName,
            SYMPTOM_TABLE: SymptomTable.tableName,
            MED_DIARY_TABLE: MedicationDiaryTable.tableName
        }

        let LambdaFunctions: lambda.Function[] = [];

        const CheckIncomingNumberFunction = new LambdaBase(this, 'CheckIncomingNumber', {
            entry: 'lambda/src',
            index: 'check_incoming_number.py',
            environment: EnvVariables
        });
        LambdaFunctions.push(CheckIncomingNumberFunction);
        PatientProfileTable.grantReadWriteData(CheckIncomingNumberFunction);

        const ConfirmReportTimeLexHandler = new LambdaBase(this, 'ConfirmReportTimeLexHandler', {
            entry: 'lambda/src',
            index: 'confirm_report_time.py',
            environment: EnvVariables
        });
        LambdaFunctions.push(ConfirmReportTimeLexHandler);

        const VerifyIdentityLexHandler = new LambdaBase(this, 'VerifyIdentityHandler', {
            entry: 'lambda/src',
            index: 'verify_identity_bot.py',
            environment: EnvVariables
        });
        LambdaFunctions.push(VerifyIdentityLexHandler);
        PatientProfileTable.grantReadWriteData(VerifyIdentityLexHandler)

        const GatherSymptomLexHandler = new LambdaBase(this, 'GatherSymptomHandler', {
            entry: 'lambda/src',
            index: 'gather_symptom_bot.py',
            environment: EnvVariables
        });
        LambdaFunctions.push(GatherSymptomLexHandler);
        SymptomTable.grantReadWriteData(GatherSymptomLexHandler);

        const MedicationDiaryHandler = new LambdaBase(this, 'MedicationDiaryHandler', {
            entry: 'lambda/src',
            index: 'medication_diary_bot.py',
            environment: EnvVariables
        })
        LambdaFunctions.push(MedicationDiaryHandler);
        MedicationDiaryTable.grantReadWriteData(MedicationDiaryHandler);

        const SurveyCompletionScannerFunction = new LambdaBase(this, 'SurveyCompletionScanner', {
            entry: 'lambda/src',
            index: 'outreach_scanner.py',
            environment: EnvVariables
        })
        LambdaFunctions.push(SurveyCompletionScannerFunction);
        TrialConfigTable.grantReadWriteData(SurveyCompletionScannerFunction);


        const InitiateOutboundCallFunction = new LambdaBase(this, 'InitiateOutboundCall', {
            entry: 'lambda/src',
            index: 'initiate_outbound_call.py',
            environment: {...EnvVariables, "CONNECT_INSTANCE_ID": "", "CONNECT_FLOW_ID": "", "SOURCE_NUMBER": ""}
        })
        const outboundCallPolicyStatement = new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: ["connect:StartOutboundVoiceContact"],
            resources: ["*"]
        });
        InitiateOutboundCallFunction.addToRolePolicy(outboundCallPolicyStatement);
        LambdaFunctions.push(InitiateOutboundCallFunction);

        for (let i = 0; i < SharedTables.length; i++) {
            let table = SharedTables[i]
            for (let j = 0; j < LambdaFunctions.length; j++) {
                let lambda = LambdaFunctions[j];
                table.grantReadWriteData(lambda);
            }
        }


        Common.output(this, "CheckIncomingNumberFunctionArn",
            CheckIncomingNumberFunction.functionArn,
            "Lambda Arn for checking incoming phone number in Connect contact flow")
        Common.output(this, "ConfirmReportTimeLexHandlerArn",
            ConfirmReportTimeLexHandler.functionArn,
            "Lambda Arn for report time confirm lex bot")
        Common.output(this, "VerifyIdentityLexHandlerArn",
            VerifyIdentityLexHandler.functionArn,
            "Lambda Arn for verify identity lex bot")
        Common.output(this, "GatherSymptomLexHandlerArn",
            GatherSymptomLexHandler.functionArn,
            "Lambda Arn for gather symptoms lex bot")
        Common.output(this, "MedicationDiaryHandlerArn",
            MedicationDiaryHandler.functionArn,
            "Lambda Arn for medication diary lex bot")


    }
}
