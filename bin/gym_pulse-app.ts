#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { GymAvailabilityStack } from '../lib/gym_pulse-stack';

const app = new cdk.App();
new GymAvailabilityStack(app, 'GymAvailabilityStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-east-1', // Hong Kong region
  },
});

app.synth();