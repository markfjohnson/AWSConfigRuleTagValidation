import botocore
import json
from rdklib import Evaluator, Evaluation, ConfigRule, ComplianceType

## NOTE this is a very CRUDE example of a custom Config Rule.   It should be used as a starting point, but don't
## get crazy using this in an important use case.

# Valid resource types: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html
APPLICABLE_RESOURCES = ['AWS::EC2::Instance', 'AWS::EC2::VPC']
requiredTag = "Project"


class TAG_ENABLED1(ConfigRule):

    # Set this to false to prevent unnecessary API calls
    delete_old_evaluations_on_scheduled_notification = False

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):
        print("Start TagValidation - Periodic 3.6")
        evaluations = self.evaluateEC2(client_factory, event)
        evaluations.extend(self.evaluateVPC(client_factory, event))
        return evaluations

    def validateTag(self, tags, tagVal):
        foundTag = False
        if tags is not None:
            for t in tags:
                if t['Key'] == tagVal:
                    foundTag = True

        return(foundTag)

    def setEvalCompliance(self, compliant, id, resourceIndex):

        if compliant:
            e = Evaluation(ComplianceType.COMPLIANT, id, APPLICABLE_RESOURCES[resourceIndex])
        else:
            e = Evaluation(ComplianceType.NON_COMPLIANT, id, APPLICABLE_RESOURCES[resourceIndex])
        return(e)

    def evaluateVPC(self, client_factory, event):
        print("Evaluate VPC")
        client = client_factory.build_client('ec2')
        evaluations = []
        try:
            vpcs = client.describe_vpcs()['Vpcs']
            print(vpcs)
            for v in vpcs:
                print(v)
                vpcId = v['VpcId']
                result = self.validateTag(v.get('Tags'), requiredTag)
                evaluations.append(self.setEvalCompliance(result, vpcId,1))
        except Exception as e:
            print(f"Exception: {e}")
        return(evaluations)

    def evaluateEC2(self, client_factory, event):
        print("Evaluate EC2")
        client = client_factory.build_client('ec2')  # Just do something like this for each resource type
        evaluations = []
        try:
            ec2_instances = client.describe_instances()['Reservations'][0]['Instances']
            for i in ec2_instances:
                ec2_id = i['InstanceId']
                result = self.validateTag(i.get('Tags'), requiredTag)
                evaluations.append(self.setEvalCompliance(result, ec2_id, 0))
        except botocore.exceptions.ClientError as error:
            # Scenario:2 SecurityHub is not enabled for an AWS Account.
            print(f"Caught exception {error}")
            if error.response['Error']['Code'] == 'InvalidAccessException':
                evaluations.append(
                    Evaluation(ComplianceType.NON_COMPLIANT, event['accountId'], APPLICABLE_RESOURCES[0]))
            else:
                raise error
        return evaluations


def lambda_handler(event, context):
    my_rule = TAG_ENABLED1()
    evaluator = Evaluator(my_rule, APPLICABLE_RESOURCES)
    return evaluator.handle(event, context)
