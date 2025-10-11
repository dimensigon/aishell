"""
AWS DynamoDB MCP Client

Provides integration with Amazon DynamoDB, supporting item operations,
batch operations, queries, scans, and table management.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class DynamoDBClient:
    """
    MCP client for AWS DynamoDB operations.

    Supports:
    - CRUD operations
    - Batch operations
    - Queries and scans
    - Table management
    - Indexes
    - Transactions
    """

    def __init__(
        self,
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize DynamoDB client

        Args:
            region_name: AWS region
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            endpoint_url: Custom endpoint (for local DynamoDB)
            **kwargs: Additional boto3 client options
        """
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.endpoint_url = endpoint_url
        self.client_options = kwargs

        self.client = None
        self.resource = None

        logger.info(
            f"Initialized DynamoDB client "
            f"(region={region_name}, endpoint={endpoint_url or 'AWS'})"
        )

    async def connect(self) -> None:
        """Establish connection to DynamoDB"""
        try:
            import boto3

            session_kwargs = {
                'region_name': self.region_name
            }

            if self.aws_access_key_id and self.aws_secret_access_key:
                session_kwargs['aws_access_key_id'] = self.aws_access_key_id
                session_kwargs['aws_secret_access_key'] = self.aws_secret_access_key

            client_kwargs = {}
            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url

            client_kwargs.update(self.client_options)

            session = boto3.Session(**session_kwargs)
            self.client = session.client('dynamodb', **client_kwargs)
            self.resource = session.resource('dynamodb', **client_kwargs)

            logger.info("Connected to DynamoDB")

        except ImportError:
            raise ImportError(
                "boto3 not installed. Install with: pip install boto3"
            )
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Close DynamoDB connection"""
        # boto3 clients don't need explicit disconnection
        self.client = None
        self.resource = None
        logger.info("Disconnected from DynamoDB")

    async def put_item(
        self,
        table_name: str,
        item: Dict[str, Any],
        condition_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Put item into table

        Args:
            table_name: Table name
            item: Item data
            condition_expression: Conditional put expression

        Returns:
            Response metadata
        """
        if not self.resource:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            table = self.resource.Table(table_name)

            kwargs = {'Item': item}
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = table.put_item(**kwargs)
            logger.debug(f"Put item into table '{table_name}'")
            return response

        except Exception as e:
            logger.error(f"Failed to put item: {e}")
            raise

    async def get_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        consistent_read: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get item from table

        Args:
            table_name: Table name
            key: Item key
            consistent_read: Use strongly consistent read

        Returns:
            Item data or None if not found
        """
        if not self.resource:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            table = self.resource.Table(table_name)
            response = table.get_item(
                Key=key,
                ConsistentRead=consistent_read
            )

            item = response.get('Item')
            if item:
                logger.debug(f"Retrieved item from table '{table_name}'")
            else:
                logger.debug(f"Item not found in table '{table_name}'")

            return item

        except Exception as e:
            logger.error(f"Failed to get item: {e}")
            raise

    async def update_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        return_values: str = "NONE"
    ) -> Dict[str, Any]:
        """
        Update item in table

        Args:
            table_name: Table name
            key: Item key
            update_expression: Update expression
            expression_attribute_values: Attribute values
            expression_attribute_names: Attribute names
            return_values: Return value option

        Returns:
            Response data
        """
        if not self.resource:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            table = self.resource.Table(table_name)

            kwargs = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ReturnValues': return_values
            }

            if expression_attribute_values:
                kwargs['ExpressionAttributeValues'] = expression_attribute_values

            if expression_attribute_names:
                kwargs['ExpressionAttributeNames'] = expression_attribute_names

            response = table.update_item(**kwargs)
            logger.debug(f"Updated item in table '{table_name}'")
            return response

        except Exception as e:
            logger.error(f"Failed to update item: {e}")
            raise

    async def delete_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        condition_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete item from table

        Args:
            table_name: Table name
            key: Item key
            condition_expression: Conditional delete expression

        Returns:
            Response metadata
        """
        if not self.resource:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            table = self.resource.Table(table_name)

            kwargs = {'Key': key}
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = table.delete_item(**kwargs)
            logger.debug(f"Deleted item from table '{table_name}'")
            return response

        except Exception as e:
            logger.error(f"Failed to delete item: {e}")
            raise

    async def query(
        self,
        table_name: str,
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        filter_expression: Optional[str] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        scan_index_forward: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query table

        Args:
            table_name: Table name
            key_condition_expression: Key condition
            expression_attribute_values: Attribute values
            filter_expression: Additional filter
            index_name: Index to query
            limit: Max items to return
            scan_index_forward: Sort order

        Returns:
            List of items
        """
        if not self.resource:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            table = self.resource.Table(table_name)

            kwargs = {
                'KeyConditionExpression': key_condition_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ScanIndexForward': scan_index_forward
            }

            if filter_expression:
                kwargs['FilterExpression'] = filter_expression

            if index_name:
                kwargs['IndexName'] = index_name

            if limit:
                kwargs['Limit'] = limit

            response = table.query(**kwargs)
            items = response.get('Items', [])

            logger.debug(
                f"Query returned {len(items)} items from table '{table_name}'"
            )
            return items

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    async def scan(
        self,
        table_name: str,
        filter_expression: Optional[str] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan table

        Args:
            table_name: Table name
            filter_expression: Filter expression
            expression_attribute_values: Attribute values
            limit: Max items to return

        Returns:
            List of items
        """
        if not self.resource:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            table = self.resource.Table(table_name)

            kwargs = {}
            if filter_expression:
                kwargs['FilterExpression'] = filter_expression

            if expression_attribute_values:
                kwargs['ExpressionAttributeValues'] = expression_attribute_values

            if limit:
                kwargs['Limit'] = limit

            response = table.scan(**kwargs)
            items = response.get('Items', [])

            logger.debug(
                f"Scan returned {len(items)} items from table '{table_name}'"
            )
            return items

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            raise

    async def batch_write(
        self,
        table_name: str,
        items: List[Dict[str, Any]],
        delete_keys: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Batch write items

        Args:
            table_name: Table name
            items: Items to put
            delete_keys: Keys to delete

        Returns:
            Response with unprocessed items
        """
        if not self.resource:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            table = self.resource.Table(table_name)

            with table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)

                if delete_keys:
                    for key in delete_keys:
                        batch.delete_item(Key=key)

            logger.info(
                f"Batch wrote {len(items)} items "
                f"{'and deleted ' + str(len(delete_keys)) + ' items' if delete_keys else ''}"
                f" to table '{table_name}'"
            )

            return {'UnprocessedItems': {}}

        except Exception as e:
            logger.error(f"Batch write failed: {e}")
            raise

    async def create_table(
        self,
        table_name: str,
        key_schema: List[Dict[str, str]],
        attribute_definitions: List[Dict[str, str]],
        billing_mode: str = "PAY_PER_REQUEST",
        provisioned_throughput: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Create table

        Args:
            table_name: Table name
            key_schema: Key schema definition
            attribute_definitions: Attribute definitions
            billing_mode: Billing mode (PAY_PER_REQUEST or PROVISIONED)
            provisioned_throughput: Throughput for PROVISIONED mode

        Returns:
            Table description
        """
        if not self.client:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            kwargs = {
                'TableName': table_name,
                'KeySchema': key_schema,
                'AttributeDefinitions': attribute_definitions,
                'BillingMode': billing_mode
            }

            if billing_mode == "PROVISIONED" and provisioned_throughput:
                kwargs['ProvisionedThroughput'] = provisioned_throughput

            response = self.client.create_table(**kwargs)
            logger.info(f"Created table '{table_name}'")
            return response

        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise

    async def delete_table(self, table_name: str) -> Dict[str, Any]:
        """Delete table"""
        if not self.client:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            response = self.client.delete_table(TableName=table_name)
            logger.info(f"Deleted table '{table_name}'")
            return response

        except Exception as e:
            logger.error(f"Failed to delete table: {e}")
            raise

    async def list_tables(self) -> List[str]:
        """List all tables"""
        if not self.client:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            response = self.client.list_tables()
            tables = response.get('TableNames', [])
            logger.debug(f"Found {len(tables)} tables")
            return tables

        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            raise

    async def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get table description"""
        if not self.client:
            raise RuntimeError("Not connected to DynamoDB")

        try:
            response = self.client.describe_table(TableName=table_name)
            return response.get('Table', {})

        except Exception as e:
            logger.error(f"Failed to describe table: {e}")
            raise

    def __enter__(self):
        """Context manager entry"""
        import asyncio
        asyncio.create_task(self.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        import asyncio
        asyncio.create_task(self.disconnect())
