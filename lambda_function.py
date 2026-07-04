import boto3
import requests
from requests_aws4auth import AWS4Auth

region = "us-east-1"
service = "es"

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

host = "https://search-pgpcc-search-domain-v2-wiu6iulyx5bv2krzjeegauyfky.aos.us-east-1.on.aws"
index = "mygoogle"
datatype = "_doc"

headers = {"Content-Type": "application/json"}
s3 = boto3.client("s3")


def bytes_to_string(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)


def list_to_string(lines):
    return " ".join(bytes_to_string(line).strip() for line in lines if line)


def generate_summary(text, max_chars=300):
    if not text:
        return ""
    clean_text = " ".join(text.split())
    return clean_text[:max_chars] + "..." if len(clean_text) > max_chars else clean_text


def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read()
        lines = body.splitlines()

        title = bytes_to_string(lines[0]) if len(lines) > 0 else key
        author = bytes_to_string(lines[1]) if len(lines) > 1 else "None"
        date = bytes_to_string(lines[2]) if len(lines) > 2 else "None"

        full_text = list_to_string(lines[3:]) if len(lines) > 3 else ""
        summary = generate_summary(full_text)

        document = {
            "Title": title,
            "Author": author,
            "Date": date,
            "Body": full_text,
            "Summary": summary
        }

        url = f"{host}/{index}/{datatype}/{key}"

        print("Indexing key:", key)
        print("Title:", title)
        print("Summary:", summary)

        response = requests.post(url, auth=awsauth, json=document, headers=headers)

        print("OpenSearch response:", response.text)

    return {
        "statusCode": 200,
        "body": "Upload to OpenSearch completed"
    }