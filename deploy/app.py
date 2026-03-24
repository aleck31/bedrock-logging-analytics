#!/usr/bin/env python3
import aws_cdk as cdk
from stack import BedrockInvocationAnalyticsStack

app = cdk.App()
BedrockInvocationAnalyticsStack(app, "BedrockInvocationAnalytics")
app.synth()
