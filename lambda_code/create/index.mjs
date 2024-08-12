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
        let requestJSON = JSON.parse(event.body);
        await dynamo
          .put({
            TableName: "all-items",
            Item: {
              itemId: requestJSON.itemId,
              price: requestJSON.price,
              name: requestJSON.name
            }
          });
        body = `Put item ${requestJSON.itemId}`;
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
