import aws_cdk as core
import aws_cdk.assertions as assertions

from gym_pulse.gym_pulse_stack import GymPulseStack

# example tests. To run these tests, uncomment this file along with the example
# resource in gym_pulse/gym_pulse_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GymPulseStack(app, "gym-pulse")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
