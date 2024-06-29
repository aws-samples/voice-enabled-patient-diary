import core = require('aws-cdk-lib');
import constructs = require('constructs');

export class Common {
    public static output(obj: constructs.Construct, name: string, value: string, desc: string) {
        new core.CfnOutput(obj, name, {
                value: value,
                description: desc
            }
        );
    }
}