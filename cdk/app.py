#!/usr/bin/env python3
import aws_cdk as cdk
from sec_documents_stack import SecDocumentsProcessingStack

app = cdk.App()
SecDocumentsProcessingStack(app, "SecDocumentsProcessingStack")
app.synth()