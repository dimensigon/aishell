"""
Comprehensive test suite for DynamoDBClient
Target: Increase coverage from 8% to 80%
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from src.mcp_clients.dynamodb_client import DynamoDBClient


class TestDynamoDBClientInitialization:
    """Test client initialization"""

    def test_init_with_minimal_config(self):
        """Test initialization with minimal configuration"""
        client = DynamoDBClient()

        assert client.region_name == "us-east-1"
        assert client.aws_access_key_id is None
        assert client.aws_secret_access_key is None
        assert client.endpoint_url is None
        assert client.client is None
        assert client.resource is None

    def test_init_with_full_config(self):
        """Test initialization with full configuration"""
        client = DynamoDBClient(
            region_name='us-west-2',
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret',
            endpoint_url='http://localhost:8000',
            max_pool_connections=50
        )

        assert client.region_name == 'us-west-2'
        assert client.aws_access_key_id == 'test_key'
        assert client.aws_secret_access_key == 'test_secret'
        assert client.endpoint_url == 'http://localhost:8000'
        assert 'max_pool_connections' in client.client_options

    def test_init_with_local_dynamodb(self):
        """Test initialization for local DynamoDB"""
        client = DynamoDBClient(endpoint_url='http://localhost:8000')

        assert client.endpoint_url == 'http://localhost:8000'


class TestDynamoDBClientConnection:
    """Test connection management"""

    @pytest.mark.asyncio
    @patch('boto3.Session')
    async def test_connect_without_credentials(self, mock_boto3):
        """Test connection without explicit credentials"""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_resource = MagicMock()

        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_session.resource.return_value = mock_resource

        client = DynamoDBClient()
        await client.connect()

        assert client.client is not None
        assert client.resource is not None
        mock_boto3.Session.assert_called_once()

    @pytest.mark.asyncio
    @patch('boto3.Session')
    async def test_connect_with_credentials(self, mock_boto3):
        """Test connection with explicit credentials"""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_resource = MagicMock()

        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_session.resource.return_value = mock_resource

        client = DynamoDBClient(
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret'
        )
        await client.connect()

        assert client.client is not None
        assert client.resource is not None

    @pytest.mark.asyncio
    @patch('boto3.Session')
    async def test_connect_with_custom_endpoint(self, mock_boto3):
        """Test connection with custom endpoint"""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_resource = MagicMock()

        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_session.resource.return_value = mock_resource

        client = DynamoDBClient(endpoint_url='http://localhost:8000')
        await client.connect()

        mock_session.client.assert_called()
        call_kwargs = mock_session.client.call_args[1]
        assert call_kwargs.get('endpoint_url') == 'http://localhost:8000'

    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing boto3"""
        with patch.dict('sys.modules', {'boto3': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'boto3'")):
                client = DynamoDBClient()

                with pytest.raises(ImportError, match="boto3 not installed"):
                    await client.connect()

    @pytest.mark.asyncio
    @patch('boto3.Session')
    async def test_connect_connection_error(self, mock_boto3):
        """Test connection failure"""
        mock_boto3.Session.side_effect = Exception("Connection failed")

        client = DynamoDBClient()

        with pytest.raises(Exception, match="Connection failed"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection"""
        client = DynamoDBClient()
        client.client = MagicMock()
        client.resource = MagicMock()

        await client.disconnect()

        assert client.client is None
        assert client.resource is None


class TestDynamoDBClientItemOperations:
    """Test item CRUD operations"""

    @pytest.mark.asyncio
    async def test_put_item(self):
        """Test item insertion"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_table.put_item.return_value = mock_response

        item = {'id': '123', 'name': 'Test Item'}
        result = await client.put_item('test_table', item)

        assert result == mock_response
        mock_table.put_item.assert_called_once_with(Item=item)

    @pytest.mark.asyncio
    async def test_put_item_with_condition(self):
        """Test conditional item insertion"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_table.put_item.return_value = mock_response

        item = {'id': '123', 'name': 'Test Item'}
        condition = "attribute_not_exists(id)"
        result = await client.put_item('test_table', item, condition)

        mock_table.put_item.assert_called_once_with(
            Item=item,
            ConditionExpression=condition
        )

    @pytest.mark.asyncio
    async def test_put_item_without_connection(self):
        """Test put_item without connection"""
        client = DynamoDBClient()

        with pytest.raises(RuntimeError, match="Not connected to DynamoDB"):
            await client.put_item('test_table', {})

    @pytest.mark.asyncio
    async def test_get_item(self):
        """Test item retrieval"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_item = {'id': '123', 'name': 'Test Item'}
        mock_table.get_item.return_value = {'Item': expected_item}

        key = {'id': '123'}
        result = await client.get_item('test_table', key)

        assert result == expected_item
        mock_table.get_item.assert_called_once_with(Key=key, ConsistentRead=False)

    @pytest.mark.asyncio
    async def test_get_item_not_found(self):
        """Test item retrieval when not found"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        mock_table.get_item.return_value = {}

        key = {'id': 'nonexistent'}
        result = await client.get_item('test_table', key)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_item_consistent_read(self):
        """Test item retrieval with consistent read"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_item = {'id': '123', 'name': 'Test Item'}
        mock_table.get_item.return_value = {'Item': expected_item}

        key = {'id': '123'}
        result = await client.get_item('test_table', key, consistent_read=True)

        mock_table.get_item.assert_called_once_with(Key=key, ConsistentRead=True)

    @pytest.mark.asyncio
    async def test_update_item(self):
        """Test item update"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        mock_response = {'Attributes': {'id': '123', 'name': 'Updated'}}
        mock_table.update_item.return_value = mock_response

        key = {'id': '123'}
        update_expr = "SET #n = :val"
        attr_values = {':val': 'Updated'}
        attr_names = {'#n': 'name'}

        result = await client.update_item(
            'test_table',
            key,
            update_expr,
            attr_values,
            attr_names,
            return_values='ALL_NEW'
        )

        assert result == mock_response
        mock_table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_item_minimal(self):
        """Test item update with minimal parameters"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_table.update_item.return_value = mock_response

        key = {'id': '123'}
        update_expr = "SET #n = :val"

        result = await client.update_item('test_table', key, update_expr)

        call_kwargs = mock_table.update_item.call_args[1]
        assert call_kwargs['Key'] == key
        assert call_kwargs['UpdateExpression'] == update_expr
        assert call_kwargs['ReturnValues'] == 'NONE'

    @pytest.mark.asyncio
    async def test_delete_item(self):
        """Test item deletion"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_table.delete_item.return_value = mock_response

        key = {'id': '123'}
        result = await client.delete_item('test_table', key)

        assert result == mock_response
        mock_table.delete_item.assert_called_once_with(Key=key)

    @pytest.mark.asyncio
    async def test_delete_item_with_condition(self):
        """Test conditional item deletion"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_table.delete_item.return_value = mock_response

        key = {'id': '123'}
        condition = "attribute_exists(id)"
        result = await client.delete_item('test_table', key, condition)

        mock_table.delete_item.assert_called_once_with(
            Key=key,
            ConditionExpression=condition
        )


class TestDynamoDBClientQueryOperations:
    """Test query and scan operations"""

    @pytest.mark.asyncio
    async def test_query_basic(self):
        """Test basic query"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '123', 'name': 'Item1'}, {'id': '124', 'name': 'Item2'}]
        mock_table.query.return_value = {'Items': expected_items}

        key_condition = "id = :id"
        attr_values = {':id': '123'}

        result = await client.query('test_table', key_condition, attr_values)

        assert result == expected_items
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_query_with_filter(self):
        """Test query with filter expression"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '123', 'name': 'Item1', 'status': 'active'}]
        mock_table.query.return_value = {'Items': expected_items}

        key_condition = "id = :id"
        attr_values = {':id': '123', ':status': 'active'}
        filter_expr = "status = :status"

        result = await client.query(
            'test_table',
            key_condition,
            attr_values,
            filter_expression=filter_expr
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_with_index(self):
        """Test query on secondary index"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '123', 'email': 'test@example.com'}]
        mock_table.query.return_value = {'Items': expected_items}

        key_condition = "email = :email"
        attr_values = {':email': 'test@example.com'}

        result = await client.query(
            'test_table',
            key_condition,
            attr_values,
            index_name='email-index'
        )

        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs['IndexName'] == 'email-index'

    @pytest.mark.asyncio
    async def test_query_with_limit(self):
        """Test query with limit"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '123'}]
        mock_table.query.return_value = {'Items': expected_items}

        key_condition = "id = :id"
        attr_values = {':id': '123'}

        result = await client.query(
            'test_table',
            key_condition,
            attr_values,
            limit=10
        )

        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs['Limit'] == 10

    @pytest.mark.asyncio
    async def test_query_descending_order(self):
        """Test query with descending sort"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '123', 'timestamp': '2'}]
        mock_table.query.return_value = {'Items': expected_items}

        key_condition = "id = :id"
        attr_values = {':id': '123'}

        result = await client.query(
            'test_table',
            key_condition,
            attr_values,
            scan_index_forward=False
        )

        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs['ScanIndexForward'] is False

    @pytest.mark.asyncio
    async def test_scan_basic(self):
        """Test basic scan"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        mock_table.scan.return_value = {'Items': expected_items}

        result = await client.scan('test_table')

        assert result == expected_items
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_scan_with_filter(self):
        """Test scan with filter"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '1', 'status': 'active'}]
        mock_table.scan.return_value = {'Items': expected_items}

        filter_expr = "status = :status"
        attr_values = {':status': 'active'}

        result = await client.scan(
            'test_table',
            filter_expression=filter_expr,
            expression_attribute_values=attr_values
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_scan_with_limit(self):
        """Test scan with limit"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        expected_items = [{'id': '1'}]
        mock_table.scan.return_value = {'Items': expected_items}

        result = await client.scan('test_table', limit=1)

        call_kwargs = mock_table.scan.call_args[1]
        assert call_kwargs['Limit'] == 1


class TestDynamoDBClientBatchOperations:
    """Test batch operations"""

    @pytest.mark.asyncio
    async def test_batch_write_items(self):
        """Test batch write of items"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_batch_writer = MagicMock()
        mock_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        items = [
            {'id': '1', 'name': 'Item1'},
            {'id': '2', 'name': 'Item2'},
            {'id': '3', 'name': 'Item3'}
        ]

        result = await client.batch_write('test_table', items)

        assert mock_batch_writer.put_item.call_count == 3
        assert result['UnprocessedItems'] == {}

    @pytest.mark.asyncio
    async def test_batch_write_with_deletes(self):
        """Test batch write with deletions"""
        client = DynamoDBClient()
        mock_table = MagicMock()
        mock_batch_writer = MagicMock()
        mock_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        client.resource = mock_resource

        items = [{'id': '1', 'name': 'Item1'}]
        delete_keys = [{'id': '2'}, {'id': '3'}]

        result = await client.batch_write('test_table', items, delete_keys)

        assert mock_batch_writer.put_item.call_count == 1
        assert mock_batch_writer.delete_item.call_count == 2


class TestDynamoDBClientTableManagement:
    """Test table management operations"""

    @pytest.mark.asyncio
    async def test_create_table_pay_per_request(self):
        """Test table creation with pay-per-request billing"""
        client = DynamoDBClient()
        mock_client = MagicMock()
        client.client = mock_client

        mock_response = {'TableDescription': {'TableName': 'test_table'}}
        mock_client.create_table.return_value = mock_response

        key_schema = [{'AttributeName': 'id', 'KeyType': 'HASH'}]
        attr_definitions = [{'AttributeName': 'id', 'AttributeType': 'S'}]

        result = await client.create_table('test_table', key_schema, attr_definitions)

        assert result == mock_response
        call_kwargs = mock_client.create_table.call_args[1]
        assert call_kwargs['BillingMode'] == 'PAY_PER_REQUEST'

    @pytest.mark.asyncio
    async def test_create_table_provisioned(self):
        """Test table creation with provisioned billing"""
        client = DynamoDBClient()
        mock_client = MagicMock()
        client.client = mock_client

        mock_response = {'TableDescription': {'TableName': 'test_table'}}
        mock_client.create_table.return_value = mock_response

        key_schema = [{'AttributeName': 'id', 'KeyType': 'HASH'}]
        attr_definitions = [{'AttributeName': 'id', 'AttributeType': 'S'}]
        throughput = {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}

        result = await client.create_table(
            'test_table',
            key_schema,
            attr_definitions,
            billing_mode='PROVISIONED',
            provisioned_throughput=throughput
        )

        call_kwargs = mock_client.create_table.call_args[1]
        assert call_kwargs['BillingMode'] == 'PROVISIONED'
        assert call_kwargs['ProvisionedThroughput'] == throughput

    @pytest.mark.asyncio
    async def test_delete_table(self):
        """Test table deletion"""
        client = DynamoDBClient()
        mock_client = MagicMock()
        client.client = mock_client

        mock_response = {'TableDescription': {'TableName': 'test_table'}}
        mock_client.delete_table.return_value = mock_response

        result = await client.delete_table('test_table')

        assert result == mock_response
        mock_client.delete_table.assert_called_once_with(TableName='test_table')

    @pytest.mark.asyncio
    async def test_list_tables(self):
        """Test listing tables"""
        client = DynamoDBClient()
        mock_client = MagicMock()
        client.client = mock_client

        mock_response = {'TableNames': ['table1', 'table2', 'table3']}
        mock_client.list_tables.return_value = mock_response

        result = await client.list_tables()

        assert result == ['table1', 'table2', 'table3']
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_describe_table(self):
        """Test table description"""
        client = DynamoDBClient()
        mock_client = MagicMock()
        client.client = mock_client

        table_info = {
            'TableName': 'test_table',
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'ItemCount': 100
        }
        mock_response = {'Table': table_info}
        mock_client.describe_table.return_value = mock_response

        result = await client.describe_table('test_table')

        assert result == table_info
        assert result['TableName'] == 'test_table'
        assert result['ItemCount'] == 100


class TestDynamoDBClientContextManager:
    """Test context manager functionality"""

    def test_context_manager_enter(self):
        """Test context manager entry"""
        client = DynamoDBClient()

        with patch('asyncio.create_task') as mock_task:
            result = client.__enter__()

            assert result == client
            mock_task.assert_called_once()

    def test_context_manager_exit(self):
        """Test context manager exit"""
        client = DynamoDBClient()

        with patch('asyncio.create_task') as mock_task:
            client.__exit__(None, None, None)

            mock_task.assert_called_once()
