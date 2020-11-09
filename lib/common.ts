import core = require('@aws-cdk/core');

export class Common {
    public static output(obj: core.Construct, name: string, value: string, desc: string) {
        new core.CfnOutput(obj, name, {
                value: value,
                description: desc
            }
        );
    }
}