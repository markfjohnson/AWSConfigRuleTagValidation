rdk create TagValidation --runtime python3.8 --maximum-frequency TwentyFour_Hours
rdk create SECURITYHUB_ENABLED --runtime python3.8 --maximum-frequency TwentyFour_Hours

rdk deploy TagValidation --rdklib-layer-arn arn:aws:lambda:us-east-1:729451883946:layer:rdklib-layer:1
