import os
# If don't want to use CDN, enter the same URL for s3 and cloud_front
cloud_front = os.environ['CDN_URL']
s3 = os.environ['S3_URL']
