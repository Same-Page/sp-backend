import os

if os.environ.get('S3_URL'):
    # If don't want to use CDN, enter the same URL for s3 and cloud_front
    s3 = os.environ['S3_URL']
    cloud_front = os.environ.get('CDN_URL', s3)

else:
    # TODO: use flask or nginx to serve static file if
    # aws s3 is not setup
    s3 = 's3_url'
    cloud_front = os.environ.get('CDN_URL', s3)
