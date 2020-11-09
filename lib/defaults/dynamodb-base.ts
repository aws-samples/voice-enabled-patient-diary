import * as cdk from '@aws-cdk/core';
import * as dynamodb from '@aws-cdk/aws-dynamodb';
import * as _ from 'underscore';

export class DynamodbBase extends dynamodb.Table {

    constructor(scope: cdk.Construct, id: string, props: dynamodb.TableProps) {
        _.defaults(props, {
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            // The cdk default removal policy is RETAIN, which means that cdk destroy will not attempt to delete
            // the new table, and it will remain in your account until manually deleted. By setting the policy to
            // DESTROY, cdk destroy will delete the table (even if it has data in it)
            removalPolicy: cdk.RemovalPolicy.DESTROY, // NOT recommended for production code
        })
        super(scope, id, props);
    }
}