import * as cdk from '@aws-cdk/core';
import {PythonFunction, PythonFunctionProps} from "@aws-cdk/aws-lambda-python"
import * as _ from 'underscore';
import * as lambda from "@aws-cdk/aws-lambda";
import {Duration} from "@aws-cdk/core";

export class LambdaBase extends PythonFunction {

    constructor(scope: cdk.Construct, id: string, props: PythonFunctionProps) {
        _.defaults(props, {
            "runtime": lambda.Runtime.PYTHON_3_7,    // execution environment
            "timeout": Duration.seconds(10),
            "handler": 'lambda_handler'
        })
        super(scope, id, props);
    }
}