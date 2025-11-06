from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class SecDocumentsProcessingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC for SageMaker HyperPod
        vpc = ec2.Vpc(
            self, "SecDocumentsVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # S3 Bucket for data storage
        data_bucket = s3.Bucket(
            self, "SecDocumentsDataBucket",
            bucket_name=f"sec-documents-data-{self.account}-{self.region}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # S3 Bucket for model artifacts
        model_bucket = s3.Bucket(
            self, "SecDocumentsModelBucket",
            bucket_name=f"sec-documents-models-{self.account}-{self.region}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # IAM Role for SageMaker
        sagemaker_role = iam.Role(
            self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
            ]
        )

        # Security Group for SageMaker
        sagemaker_sg = ec2.SecurityGroup(
            self, "SageMakerSecurityGroup",
            vpc=vpc,
            description="Security group for SageMaker HyperPod",
            allow_all_outbound=True
        )

        # Outputs
        CfnOutput(self, "VPCId", value=vpc.vpc_id)
        CfnOutput(self, "DataBucketName", value=data_bucket.bucket_name)
        CfnOutput(self, "ModelBucketName", value=model_bucket.bucket_name)
        CfnOutput(self, "SageMakerRoleArn", value=sagemaker_role.role_arn)
        CfnOutput(self, "SecurityGroupId", value=sagemaker_sg.security_group_id)