#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import {EproVoiceStack} from '../lib/epro-voice-stack';

let config = require('../config.json');
let env = {account: config.account, region: config.region};

const app = new cdk.App();
new EproVoiceStack(app, 'EproVoiceStack', {
    env: env,
      description: "Accelerator meant to showcase a voice enabled patient diary prototype ('uksb-1tsflhn9s')",
});
