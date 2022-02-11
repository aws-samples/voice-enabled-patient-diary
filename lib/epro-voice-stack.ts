import * as cdk from '@aws-cdk/core';
import * as lambda from '@aws-cdk/aws-lambda';
import * as dynamodb from '@aws-cdk/aws-dynamodb';
//import { AwsCustomResource } from '@aws-cdk/custom-resources';

const iam = require('@aws-cdk/aws-iam');

import {Common} from './common';
import {Seeder} from 'aws-cdk-dynamodb-seeder';
import {Duration} from "@aws-cdk/core";

export class EproVoiceStack extends cdk.Stack {
    constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        let SharedTables: dynamodb.Table[] = [];
        const MedicationDiaryTable = new dynamodb.Table(this, 'MedicationDiary', {
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Time_Reported', type: dynamodb.AttributeType.STRING},
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: cdk.RemovalPolicy.DESTROY //Change to RETAIN for Production
        });

        MedicationDiaryTable.addGlobalSecondaryIndex({
            indexName: 'Patient_taken',
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Time_Reported', type: dynamodb.AttributeType.STRING}
        });

        const SymptomTable = new dynamodb.Table(this, 'Symptoms', {
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Time_Reported', type: dynamodb.AttributeType.STRING},
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: cdk.RemovalPolicy.DESTROY //Change to RETAIN for Production
        });

        const SurveyCompletionTable = new dynamodb.Table(this, 'SurveyCompletion', {
            tableName:"SurveyCompletion",
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            sortKey: {name: 'Report_Date', type: dynamodb.AttributeType.STRING},
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: cdk.RemovalPolicy.DESTROY //Change to RETAIN for Production
        })
        SharedTables.push(SurveyCompletionTable)

        const TrialConfigTable = new dynamodb.Table(this, 'TrialConfig', {
            tableName:"TrialConfig",
            partitionKey: {name: 'Trial_ID', type: dynamodb.AttributeType.STRING},
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: cdk.RemovalPolicy.DESTROY //Change to RETAIN for Production
        })

             new Seeder(this, "TrialConfigSeeder", {
            table: TrialConfigTable,
            setup: require("./ddb-seed/trial-config-setup.json"),
            teardown: require("./ddb-seed/trial-config-teardown.json"),
            refreshOnUpdate: true,  // runs setup and teardown on every update, default false
        });

        const PatientProfileTable = new dynamodb.Table(this, 'PatientProfile', {
            tableName:"PatientProfile",
            partitionKey: {name: 'Patient_ID', type: dynamodb.AttributeType.STRING},
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: cdk.RemovalPolicy.DESTROY //Change to RETAIN for Production
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

        const CheckIncomingNumberFunction = new lambda.Function(this, 'CheckIncomingNumber', {
            code: lambda.Code.fromAsset('./lambda/src'),
            handler: "check_incoming_number.lambda_handler",
            runtime:lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(30),
            environment: EnvVariables
        });
        LambdaFunctions.push(CheckIncomingNumberFunction);
        PatientProfileTable.grantReadWriteData(CheckIncomingNumberFunction);

        const ConfirmReportTimeLexHandler = new lambda.Function(this, 'ConfirmReportTimeLexHandler',
            {
                code: lambda.Code.fromAsset('./lambda/src'),
                handler: "confirm_report_time.lambda_handler",
                runtime:lambda.Runtime.PYTHON_3_9,
                timeout: Duration.seconds(30),

            environment: EnvVariables
        });
        LambdaFunctions.push(ConfirmReportTimeLexHandler);

        const VerifyIdentityLexHandler = new lambda.Function(this, 'VerifyIdentityHandler', {
            code: lambda.Code.fromAsset('./lambda/src'),
            handler: "verify_identity_bot.lambda_handler",
            runtime:lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(30),
            environment: EnvVariables
        });
        LambdaFunctions.push(VerifyIdentityLexHandler);
        PatientProfileTable.grantReadWriteData(VerifyIdentityLexHandler)

        const GatherSymptomLexHandler = new lambda.Function(this, 'GatherSymptomHandler', {
            code: lambda.Code.fromAsset('./lambda/src'),
            handler: "gather_symptom_bot.lambda_handler",
            runtime:lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(30),
            environment: EnvVariables
        });
        LambdaFunctions.push(GatherSymptomLexHandler);
        SymptomTable.grantReadWriteData(GatherSymptomLexHandler);

        const MedicationDiaryHandler = new lambda.Function(this, 'MedicationDiaryHandler', {
            code: lambda.Code.fromAsset('./lambda/src'),
            handler: "medication_diary_bot.lambda_handler",
            runtime:lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(30),
            environment: EnvVariables
        })
        LambdaFunctions.push(MedicationDiaryHandler);
        MedicationDiaryTable.grantReadWriteData(MedicationDiaryHandler);

        const SurveyCompletionScannerFunction = new lambda.Function(this, 'SurveyCompletionScanner', {
            code: lambda.Code.fromAsset('./lambda/src'),
            handler: "outreach_scanner.lambda_handler",
            runtime:lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(30),
            environment: EnvVariables
        })
        LambdaFunctions.push(SurveyCompletionScannerFunction);
        TrialConfigTable.grantReadWriteData(SurveyCompletionScannerFunction);

        const InitiateOutboundCallFunction = new lambda.Function(this,'InitiateOutboundCall',
            {
                code: lambda.Code.fromAsset('./lambda/src'),
                runtime:lambda.Runtime.PYTHON_3_9,
                timeout: Duration.seconds(10),
                handler: "initiate_outbound_call.lambda_handler"
            }) ;

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
