import { expect as expectCDK, matchTemplate, MatchStyle } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import * as EproVoice from '../lib/epro-voice-stack';

test('Empty Stack', () => {
    const app = new cdk.App();
    // WHEN
    const stack = new EproVoice.EproVoiceStack(app, 'MyTestStack');
    // THEN
    expectCDK(stack).to(matchTemplate({
      "Resources": {}
    }, MatchStyle.EXACT))
});
