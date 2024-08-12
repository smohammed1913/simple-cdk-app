import { DynamoDB } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';

const dynamo = DynamoDBDocument.from(new DynamoDB());


export const handler = async (event) => {
  let body;
  let statusCode = 200;
  const headers = {
    "Content-Type": "application/json"
  };
  console.log(JSON.stringify(event));

  try {
        await dynamo
          .delete({
            TableName: "all-items",
            Key: {
              itemId: event.pathParameters.id
            }
          });
        body = `Deleted item ${event.pathParameters.id}`;

  } catch (err) {
    statusCode = 400;
    body = err.message;
  } finally {
    body = JSON.stringify(body);
  }

  return {
    statusCode,
    body,
    headers
  };
};
