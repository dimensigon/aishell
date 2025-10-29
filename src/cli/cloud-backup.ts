/**
 * Cloud Backup Service
 * Provides cloud storage integration for backups (AWS S3, Azure Blob, Google Cloud Storage)
 * Supports upload, download, list, and delete operations across multiple cloud providers
 */

import { createLogger } from '../core/logger';
import * as fs from 'fs/promises';
import * as path from 'path';
import { createReadStream, createWriteStream } from 'fs';
import { Readable } from 'stream';
import { pipeline } from 'stream/promises';

const logger = createLogger('CloudBackup');

/**
 * Cloud provider types
 */
export enum CloudProvider {
  AWS_S3 = 'aws-s3',
  AZURE_BLOB = 'azure-blob',
  GOOGLE_CLOUD = 'google-cloud',
  LOCAL = 'local'
}

/**
 * AWS S3 configuration
 */
export interface S3Config {
  bucket: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  prefix?: string;
  storageClass?: 'STANDARD' | 'INTELLIGENT_TIERING' | 'GLACIER' | 'DEEP_ARCHIVE';
}

/**
 * Azure Blob configuration
 */
export interface AzureBlobConfig {
  accountName: string;
  accountKey: string;
  containerName: string;
  prefix?: string;
  tier?: 'Hot' | 'Cool' | 'Archive';
}

/**
 * Google Cloud Storage configuration
 */
export interface GcsConfig {
  projectId: string;
  keyFilename: string;
  bucketName: string;
  prefix?: string;
  storageClass?: 'STANDARD' | 'NEARLINE' | 'COLDLINE' | 'ARCHIVE';
}

/**
 * Cloud storage configuration union type
 */
export type CloudStorageConfig = S3Config | AzureBlobConfig | GcsConfig;

/**
 * Upload options
 */
export interface UploadOptions {
  metadata?: Record<string, string>;
  encryption?: boolean;
  multipartThreshold?: number; // Size in bytes to use multipart upload
  concurrency?: number; // Number of concurrent upload parts
  progressCallback?: (progress: number) => void;
}

/**
 * Download options
 */
export interface DownloadOptions {
  destination?: string;
  progressCallback?: (progress: number) => void;
}

/**
 * Cloud object metadata
 */
export interface CloudObjectMetadata {
  key: string;
  size: number;
  lastModified: Date;
  etag?: string;
  metadata?: Record<string, string>;
  storageClass?: string;
}

/**
 * List options
 */
export interface ListOptions {
  prefix?: string;
  maxKeys?: number;
  continuationToken?: string;
}

/**
 * List result
 */
export interface ListResult {
  objects: CloudObjectMetadata[];
  isTruncated: boolean;
  continuationToken?: string;
}

/**
 * Cloud Backup Service
 * Abstract base class for cloud storage providers
 */
export abstract class CloudBackupService {
  constructor(
    protected provider: CloudProvider,
    protected config: CloudStorageConfig
  ) {}

  /**
   * Upload file to cloud storage
   */
  abstract upload(
    localPath: string,
    remotePath: string,
    options?: UploadOptions
  ): Promise<CloudObjectMetadata>;

  /**
   * Download file from cloud storage
   */
  abstract download(
    remotePath: string,
    localPath: string,
    options?: DownloadOptions
  ): Promise<void>;

  /**
   * List objects in cloud storage
   */
  abstract list(options?: ListOptions): Promise<ListResult>;

  /**
   * Delete object from cloud storage
   */
  abstract delete(remotePath: string): Promise<void>;

  /**
   * Check if object exists
   */
  abstract exists(remotePath: string): Promise<boolean>;

  /**
   * Get object metadata
   */
  abstract getMetadata(remotePath: string): Promise<CloudObjectMetadata>;

  /**
   * Copy object within cloud storage
   */
  abstract copy(sourcePath: string, destinationPath: string): Promise<void>;
}

/**
 * AWS S3 Backup Service
 */
export class S3BackupService extends CloudBackupService {
  private s3Client: any;

  constructor(config: S3Config) {
    super(CloudProvider.AWS_S3, config);
    this.initializeS3Client();
  }

  private initializeS3Client(): void {
    // Initialize AWS S3 client (using AWS SDK v3)
    // NOTE: In production, install @aws-sdk/client-s3
    try {
      // Lazy load AWS SDK to avoid dependency if not needed
      const { S3Client } = require('@aws-sdk/client-s3');
      const s3Config = this.config as S3Config;

      this.s3Client = new S3Client({
        region: s3Config.region,
        credentials: {
          accessKeyId: s3Config.accessKeyId,
          secretAccessKey: s3Config.secretAccessKey
        }
      });

      logger.info('S3 client initialized', {
        region: s3Config.region,
        bucket: s3Config.bucket
      });
    } catch (error) {
      logger.warn('AWS SDK not available - install @aws-sdk/client-s3 for S3 support', { error });
      this.s3Client = null;
    }
  }

  async upload(
    localPath: string,
    remotePath: string,
    options: UploadOptions = {}
  ): Promise<CloudObjectMetadata> {
    if (!this.s3Client) {
      throw new Error('AWS SDK not available - install @aws-sdk/client-s3');
    }

    const s3Config = this.config as S3Config;
    const key = s3Config.prefix ? `${s3Config.prefix}/${remotePath}` : remotePath;

    try {
      logger.info('Uploading to S3', { localPath, key });

      const fileStats = await fs.stat(localPath);
      const fileStream = createReadStream(localPath);

      // Use multipart upload for large files
      const multipartThreshold = options.multipartThreshold || 100 * 1024 * 1024; // 100MB

      if (fileStats.size > multipartThreshold) {
        return await this.multipartUpload(localPath, key, fileStats.size, options);
      }

      // Regular upload for smaller files
      const { PutObjectCommand } = require('@aws-sdk/client-s3');

      const uploadParams = {
        Bucket: s3Config.bucket,
        Key: key,
        Body: fileStream,
        Metadata: options.metadata,
        StorageClass: s3Config.storageClass || 'STANDARD',
        ServerSideEncryption: options.encryption ? 'AES256' : undefined
      };

      const response = await this.s3Client.send(new PutObjectCommand(uploadParams));

      logger.info('S3 upload completed', { key, size: fileStats.size });

      return {
        key,
        size: fileStats.size,
        lastModified: new Date(),
        etag: response.ETag,
        metadata: options.metadata,
        storageClass: s3Config.storageClass
      };
    } catch (error) {
      logger.error('S3 upload failed', error, { localPath, key });
      throw error;
    }
  }

  private async multipartUpload(
    localPath: string,
    key: string,
    fileSize: number,
    options: UploadOptions
  ): Promise<CloudObjectMetadata> {
    const {
      CreateMultipartUploadCommand,
      UploadPartCommand,
      CompleteMultipartUploadCommand,
      AbortMultipartUploadCommand
    } = require('@aws-sdk/client-s3');

    const s3Config = this.config as S3Config;
    const partSize = 10 * 1024 * 1024; // 10MB parts
    const numParts = Math.ceil(fileSize / partSize);

    logger.info('Starting multipart upload', { key, fileSize, numParts });

    try {
      // Initiate multipart upload
      const createResponse = await this.s3Client.send(new CreateMultipartUploadCommand({
        Bucket: s3Config.bucket,
        Key: key,
        Metadata: options.metadata,
        StorageClass: s3Config.storageClass || 'STANDARD',
        ServerSideEncryption: options.encryption ? 'AES256' : undefined
      }));

      const uploadId = createResponse.UploadId;
      const parts: any[] = [];

      // Upload parts
      const fileHandle = await fs.open(localPath, 'r');

      for (let partNumber = 1; partNumber <= numParts; partNumber++) {
        const start = (partNumber - 1) * partSize;
        const end = Math.min(start + partSize, fileSize);
        const buffer = Buffer.alloc(end - start);

        await fileHandle.read(buffer, 0, buffer.length, start);

        const uploadPartResponse = await this.s3Client.send(new UploadPartCommand({
          Bucket: s3Config.bucket,
          Key: key,
          UploadId: uploadId,
          PartNumber: partNumber,
          Body: buffer
        }));

        parts.push({
          PartNumber: partNumber,
          ETag: uploadPartResponse.ETag
        });

        // Report progress
        if (options.progressCallback) {
          const progress = (partNumber / numParts) * 100;
          options.progressCallback(progress);
        }

        logger.debug('Uploaded part', { partNumber, numParts });
      }

      await fileHandle.close();

      // Complete multipart upload
      const completeResponse = await this.s3Client.send(new CompleteMultipartUploadCommand({
        Bucket: s3Config.bucket,
        Key: key,
        UploadId: uploadId,
        MultipartUpload: { Parts: parts }
      }));

      logger.info('Multipart upload completed', { key, parts: parts.length });

      return {
        key,
        size: fileSize,
        lastModified: new Date(),
        etag: completeResponse.ETag,
        metadata: options.metadata,
        storageClass: s3Config.storageClass
      };
    } catch (error) {
      logger.error('Multipart upload failed', error, { key });
      throw error;
    }
  }

  async download(
    remotePath: string,
    localPath: string,
    options: DownloadOptions = {}
  ): Promise<void> {
    if (!this.s3Client) {
      throw new Error('AWS SDK not available - install @aws-sdk/client-s3');
    }

    const s3Config = this.config as S3Config;
    const key = s3Config.prefix ? `${s3Config.prefix}/${remotePath}` : remotePath;

    try {
      logger.info('Downloading from S3', { key, localPath });

      const { GetObjectCommand } = require('@aws-sdk/client-s3');

      const response = await this.s3Client.send(new GetObjectCommand({
        Bucket: s3Config.bucket,
        Key: key
      }));

      // Ensure directory exists
      await fs.mkdir(path.dirname(localPath), { recursive: true });

      // Stream to file
      const writeStream = createWriteStream(localPath);
      await pipeline(response.Body as Readable, writeStream);

      logger.info('S3 download completed', { key, localPath });
    } catch (error) {
      logger.error('S3 download failed', error, { key, localPath });
      throw error;
    }
  }

  async list(options: ListOptions = {}): Promise<ListResult> {
    if (!this.s3Client) {
      throw new Error('AWS SDK not available - install @aws-sdk/client-s3');
    }

    const s3Config = this.config as S3Config;
    const { ListObjectsV2Command } = require('@aws-sdk/client-s3');

    try {
      const prefix = options.prefix || s3Config.prefix || '';

      const response = await this.s3Client.send(new ListObjectsV2Command({
        Bucket: s3Config.bucket,
        Prefix: prefix,
        MaxKeys: options.maxKeys || 1000,
        ContinuationToken: options.continuationToken
      }));

      const objects: CloudObjectMetadata[] = (response.Contents || []).map((obj: any) => ({
        key: obj.Key,
        size: obj.Size,
        lastModified: obj.LastModified,
        etag: obj.ETag,
        storageClass: obj.StorageClass
      }));

      return {
        objects,
        isTruncated: response.IsTruncated || false,
        continuationToken: response.NextContinuationToken
      };
    } catch (error) {
      logger.error('S3 list failed', error);
      throw error;
    }
  }

  async delete(remotePath: string): Promise<void> {
    if (!this.s3Client) {
      throw new Error('AWS SDK not available - install @aws-sdk/client-s3');
    }

    const s3Config = this.config as S3Config;
    const key = s3Config.prefix ? `${s3Config.prefix}/${remotePath}` : remotePath;

    try {
      const { DeleteObjectCommand } = require('@aws-sdk/client-s3');

      await this.s3Client.send(new DeleteObjectCommand({
        Bucket: s3Config.bucket,
        Key: key
      }));

      logger.info('S3 object deleted', { key });
    } catch (error) {
      logger.error('S3 delete failed', error, { key });
      throw error;
    }
  }

  async exists(remotePath: string): Promise<boolean> {
    if (!this.s3Client) {
      throw new Error('AWS SDK not available - install @aws-sdk/client-s3');
    }

    const s3Config = this.config as S3Config;
    const key = s3Config.prefix ? `${s3Config.prefix}/${remotePath}` : remotePath;

    try {
      const { HeadObjectCommand } = require('@aws-sdk/client-s3');

      await this.s3Client.send(new HeadObjectCommand({
        Bucket: s3Config.bucket,
        Key: key
      }));

      return true;
    } catch (error: any) {
      if (error.name === 'NotFound' || error.$metadata?.httpStatusCode === 404) {
        return false;
      }
      throw error;
    }
  }

  async getMetadata(remotePath: string): Promise<CloudObjectMetadata> {
    if (!this.s3Client) {
      throw new Error('AWS SDK not available - install @aws-sdk/client-s3');
    }

    const s3Config = this.config as S3Config;
    const key = s3Config.prefix ? `${s3Config.prefix}/${remotePath}` : remotePath;

    try {
      const { HeadObjectCommand } = require('@aws-sdk/client-s3');

      const response = await this.s3Client.send(new HeadObjectCommand({
        Bucket: s3Config.bucket,
        Key: key
      }));

      return {
        key,
        size: response.ContentLength || 0,
        lastModified: response.LastModified || new Date(),
        etag: response.ETag,
        metadata: response.Metadata,
        storageClass: response.StorageClass
      };
    } catch (error) {
      logger.error('Failed to get S3 metadata', error, { key });
      throw error;
    }
  }

  async copy(sourcePath: string, destinationPath: string): Promise<void> {
    if (!this.s3Client) {
      throw new Error('AWS SDK not available - install @aws-sdk/client-s3');
    }

    const s3Config = this.config as S3Config;
    const sourceKey = s3Config.prefix ? `${s3Config.prefix}/${sourcePath}` : sourcePath;
    const destKey = s3Config.prefix ? `${s3Config.prefix}/${destinationPath}` : destinationPath;

    try {
      const { CopyObjectCommand } = require('@aws-sdk/client-s3');

      await this.s3Client.send(new CopyObjectCommand({
        Bucket: s3Config.bucket,
        CopySource: `${s3Config.bucket}/${sourceKey}`,
        Key: destKey
      }));

      logger.info('S3 object copied', { sourceKey, destKey });
    } catch (error) {
      logger.error('S3 copy failed', error, { sourceKey, destKey });
      throw error;
    }
  }
}

/**
 * Azure Blob Storage Backup Service
 */
export class AzureBlobBackupService extends CloudBackupService {
  private blobServiceClient: any;

  constructor(config: AzureBlobConfig) {
    super(CloudProvider.AZURE_BLOB, config);
    this.initializeAzureClient();
  }

  private initializeAzureClient(): void {
    try {
      const { BlobServiceClient, StorageSharedKeyCredential } = require('@azure/storage-blob');
      const azureConfig = this.config as AzureBlobConfig;

      const sharedKeyCredential = new StorageSharedKeyCredential(
        azureConfig.accountName,
        azureConfig.accountKey
      );

      this.blobServiceClient = new BlobServiceClient(
        `https://${azureConfig.accountName}.blob.core.windows.net`,
        sharedKeyCredential
      );

      logger.info('Azure Blob client initialized', {
        accountName: azureConfig.accountName,
        container: azureConfig.containerName
      });
    } catch (error) {
      logger.warn('Azure Storage SDK not available - install @azure/storage-blob', { error });
      this.blobServiceClient = null;
    }
  }

  async upload(
    localPath: string,
    remotePath: string,
    options: UploadOptions = {}
  ): Promise<CloudObjectMetadata> {
    if (!this.blobServiceClient) {
      throw new Error('Azure SDK not available - install @azure/storage-blob');
    }

    const azureConfig = this.config as AzureBlobConfig;
    const blobName = azureConfig.prefix ? `${azureConfig.prefix}/${remotePath}` : remotePath;

    try {
      logger.info('Uploading to Azure Blob', { localPath, blobName });

      const containerClient = this.blobServiceClient.getContainerClient(azureConfig.containerName);
      const blockBlobClient = containerClient.getBlockBlobClient(blobName);

      const fileStats = await fs.stat(localPath);

      await blockBlobClient.uploadFile(localPath, {
        metadata: options.metadata,
        tier: azureConfig.tier,
        blobHTTPHeaders: {
          blobContentType: 'application/octet-stream'
        }
      });

      logger.info('Azure Blob upload completed', { blobName, size: fileStats.size });

      return {
        key: blobName,
        size: fileStats.size,
        lastModified: new Date(),
        metadata: options.metadata
      };
    } catch (error) {
      logger.error('Azure Blob upload failed', error, { localPath, blobName });
      throw error;
    }
  }

  async download(
    remotePath: string,
    localPath: string,
    _options: DownloadOptions = {}
  ): Promise<void> {
    if (!this.blobServiceClient) {
      throw new Error('Azure SDK not available - install @azure/storage-blob');
    }

    const azureConfig = this.config as AzureBlobConfig;
    const blobName = azureConfig.prefix ? `${azureConfig.prefix}/${remotePath}` : remotePath;

    try {
      logger.info('Downloading from Azure Blob', { blobName, localPath });

      const containerClient = this.blobServiceClient.getContainerClient(azureConfig.containerName);
      const blockBlobClient = containerClient.getBlockBlobClient(blobName);

      await fs.mkdir(path.dirname(localPath), { recursive: true });
      await blockBlobClient.downloadToFile(localPath);

      logger.info('Azure Blob download completed', { blobName, localPath });
    } catch (error) {
      logger.error('Azure Blob download failed', error, { blobName, localPath });
      throw error;
    }
  }

  async list(options: ListOptions = {}): Promise<ListResult> {
    if (!this.blobServiceClient) {
      throw new Error('Azure SDK not available - install @azure/storage-blob');
    }

    const azureConfig = this.config as AzureBlobConfig;

    try {
      const containerClient = this.blobServiceClient.getContainerClient(azureConfig.containerName);
      const prefix = options.prefix || azureConfig.prefix || '';

      const objects: CloudObjectMetadata[] = [];
      const iterator = containerClient.listBlobsFlat({ prefix });

      for await (const blob of iterator) {
        objects.push({
          key: blob.name,
          size: blob.properties.contentLength || 0,
          lastModified: blob.properties.lastModified || new Date(),
          etag: blob.properties.etag,
          metadata: blob.metadata
        });

        if (options.maxKeys && objects.length >= options.maxKeys) {
          break;
        }
      }

      return {
        objects,
        isTruncated: false
      };
    } catch (error) {
      logger.error('Azure Blob list failed', error);
      throw error;
    }
  }

  async delete(remotePath: string): Promise<void> {
    if (!this.blobServiceClient) {
      throw new Error('Azure SDK not available - install @azure/storage-blob');
    }

    const azureConfig = this.config as AzureBlobConfig;
    const blobName = azureConfig.prefix ? `${azureConfig.prefix}/${remotePath}` : remotePath;

    try {
      const containerClient = this.blobServiceClient.getContainerClient(azureConfig.containerName);
      const blockBlobClient = containerClient.getBlockBlobClient(blobName);

      await blockBlobClient.delete();

      logger.info('Azure Blob deleted', { blobName });
    } catch (error) {
      logger.error('Azure Blob delete failed', error, { blobName });
      throw error;
    }
  }

  async exists(remotePath: string): Promise<boolean> {
    if (!this.blobServiceClient) {
      throw new Error('Azure SDK not available - install @azure/storage-blob');
    }

    const azureConfig = this.config as AzureBlobConfig;
    const blobName = azureConfig.prefix ? `${azureConfig.prefix}/${remotePath}` : remotePath;

    try {
      const containerClient = this.blobServiceClient.getContainerClient(azureConfig.containerName);
      const blockBlobClient = containerClient.getBlockBlobClient(blobName);

      return await blockBlobClient.exists();
    } catch (error) {
      logger.error('Failed to check Azure Blob existence', error, { blobName });
      return false;
    }
  }

  async getMetadata(remotePath: string): Promise<CloudObjectMetadata> {
    if (!this.blobServiceClient) {
      throw new Error('Azure SDK not available - install @azure/storage-blob');
    }

    const azureConfig = this.config as AzureBlobConfig;
    const blobName = azureConfig.prefix ? `${azureConfig.prefix}/${remotePath}` : remotePath;

    try {
      const containerClient = this.blobServiceClient.getContainerClient(azureConfig.containerName);
      const blockBlobClient = containerClient.getBlockBlobClient(blobName);

      const properties = await blockBlobClient.getProperties();

      return {
        key: blobName,
        size: properties.contentLength || 0,
        lastModified: properties.lastModified || new Date(),
        etag: properties.etag,
        metadata: properties.metadata
      };
    } catch (error) {
      logger.error('Failed to get Azure Blob metadata', error, { blobName });
      throw error;
    }
  }

  async copy(sourcePath: string, destinationPath: string): Promise<void> {
    if (!this.blobServiceClient) {
      throw new Error('Azure SDK not available - install @azure/storage-blob');
    }

    const azureConfig = this.config as AzureBlobConfig;
    const sourceBlobName = azureConfig.prefix ? `${azureConfig.prefix}/${sourcePath}` : sourcePath;
    const destBlobName = azureConfig.prefix ? `${azureConfig.prefix}/${destinationPath}` : destinationPath;

    try {
      const containerClient = this.blobServiceClient.getContainerClient(azureConfig.containerName);
      const sourceClient = containerClient.getBlockBlobClient(sourceBlobName);
      const destClient = containerClient.getBlockBlobClient(destBlobName);

      const sourceUrl = sourceClient.url;
      await destClient.beginCopyFromURL(sourceUrl);

      logger.info('Azure Blob copied', { sourceBlobName, destBlobName });
    } catch (error) {
      logger.error('Azure Blob copy failed', error, { sourceBlobName, destBlobName });
      throw error;
    }
  }
}

/**
 * Google Cloud Storage Backup Service
 */
export class GcsBackupService extends CloudBackupService {
  private storage: any;
  private bucket: any;

  constructor(config: GcsConfig) {
    super(CloudProvider.GOOGLE_CLOUD, config);
    this.initializeGcsClient();
  }

  private initializeGcsClient(): void {
    try {
      const { Storage } = require('@google-cloud/storage');
      const gcsConfig = this.config as GcsConfig;

      this.storage = new Storage({
        projectId: gcsConfig.projectId,
        keyFilename: gcsConfig.keyFilename
      });

      this.bucket = this.storage.bucket(gcsConfig.bucketName);

      logger.info('GCS client initialized', {
        projectId: gcsConfig.projectId,
        bucket: gcsConfig.bucketName
      });
    } catch (error) {
      logger.warn('Google Cloud SDK not available - install @google-cloud/storage', { error });
      this.storage = null;
    }
  }

  async upload(
    localPath: string,
    remotePath: string,
    options: UploadOptions = {}
  ): Promise<CloudObjectMetadata> {
    if (!this.storage) {
      throw new Error('Google Cloud SDK not available - install @google-cloud/storage');
    }

    const gcsConfig = this.config as GcsConfig;
    const objectName = gcsConfig.prefix ? `${gcsConfig.prefix}/${remotePath}` : remotePath;

    try {
      logger.info('Uploading to GCS', { localPath, objectName });

      const file = this.bucket.file(objectName);
      const fileStats = await fs.stat(localPath);

      await file.save(await fs.readFile(localPath), {
        metadata: {
          metadata: options.metadata,
          contentType: 'application/octet-stream'
        },
        resumable: fileStats.size > 10 * 1024 * 1024 // Use resumable upload for files > 10MB
      });

      logger.info('GCS upload completed', { objectName, size: fileStats.size });

      return {
        key: objectName,
        size: fileStats.size,
        lastModified: new Date(),
        metadata: options.metadata
      };
    } catch (error) {
      logger.error('GCS upload failed', error, { localPath, objectName });
      throw error;
    }
  }

  async download(
    remotePath: string,
    localPath: string,
    _options: DownloadOptions = {}
  ): Promise<void> {
    if (!this.storage) {
      throw new Error('Google Cloud SDK not available - install @google-cloud/storage');
    }

    const gcsConfig = this.config as GcsConfig;
    const objectName = gcsConfig.prefix ? `${gcsConfig.prefix}/${remotePath}` : remotePath;

    try {
      logger.info('Downloading from GCS', { objectName, localPath });

      const file = this.bucket.file(objectName);
      await fs.mkdir(path.dirname(localPath), { recursive: true });
      await file.download({ destination: localPath });

      logger.info('GCS download completed', { objectName, localPath });
    } catch (error) {
      logger.error('GCS download failed', error, { objectName, localPath });
      throw error;
    }
  }

  async list(options: ListOptions = {}): Promise<ListResult> {
    if (!this.storage) {
      throw new Error('Google Cloud SDK not available - install @google-cloud/storage');
    }

    const gcsConfig = this.config as GcsConfig;

    try {
      const prefix = options.prefix || gcsConfig.prefix || '';

      const [files] = await this.bucket.getFiles({
        prefix,
        maxResults: options.maxKeys
      });

      const objects: CloudObjectMetadata[] = files.map((file: any) => ({
        key: file.name,
        size: parseInt(file.metadata.size, 10),
        lastModified: new Date(file.metadata.updated),
        etag: file.metadata.etag,
        metadata: file.metadata.metadata,
        storageClass: file.metadata.storageClass
      }));

      return {
        objects,
        isTruncated: false
      };
    } catch (error) {
      logger.error('GCS list failed', error);
      throw error;
    }
  }

  async delete(remotePath: string): Promise<void> {
    if (!this.storage) {
      throw new Error('Google Cloud SDK not available - install @google-cloud/storage');
    }

    const gcsConfig = this.config as GcsConfig;
    const objectName = gcsConfig.prefix ? `${gcsConfig.prefix}/${remotePath}` : remotePath;

    try {
      const file = this.bucket.file(objectName);
      await file.delete();

      logger.info('GCS object deleted', { objectName });
    } catch (error) {
      logger.error('GCS delete failed', error, { objectName });
      throw error;
    }
  }

  async exists(remotePath: string): Promise<boolean> {
    if (!this.storage) {
      throw new Error('Google Cloud SDK not available - install @google-cloud/storage');
    }

    const gcsConfig = this.config as GcsConfig;
    const objectName = gcsConfig.prefix ? `${gcsConfig.prefix}/${remotePath}` : remotePath;

    try {
      const file = this.bucket.file(objectName);
      const [exists] = await file.exists();
      return exists;
    } catch (error) {
      logger.error('Failed to check GCS existence', error, { objectName });
      return false;
    }
  }

  async getMetadata(remotePath: string): Promise<CloudObjectMetadata> {
    if (!this.storage) {
      throw new Error('Google Cloud SDK not available - install @google-cloud/storage');
    }

    const gcsConfig = this.config as GcsConfig;
    const objectName = gcsConfig.prefix ? `${gcsConfig.prefix}/${remotePath}` : remotePath;

    try {
      const file = this.bucket.file(objectName);
      const [metadata] = await file.getMetadata();

      return {
        key: objectName,
        size: parseInt(metadata.size, 10),
        lastModified: new Date(metadata.updated),
        etag: metadata.etag,
        metadata: metadata.metadata,
        storageClass: metadata.storageClass
      };
    } catch (error) {
      logger.error('Failed to get GCS metadata', error, { objectName });
      throw error;
    }
  }

  async copy(sourcePath: string, destinationPath: string): Promise<void> {
    if (!this.storage) {
      throw new Error('Google Cloud SDK not available - install @google-cloud/storage');
    }

    const gcsConfig = this.config as GcsConfig;
    const sourceObjectName = gcsConfig.prefix ? `${gcsConfig.prefix}/${sourcePath}` : sourcePath;
    const destObjectName = gcsConfig.prefix ? `${gcsConfig.prefix}/${destinationPath}` : destinationPath;

    try {
      const sourceFile = this.bucket.file(sourceObjectName);
      const destFile = this.bucket.file(destObjectName);

      await sourceFile.copy(destFile);

      logger.info('GCS object copied', { sourceObjectName, destObjectName });
    } catch (error) {
      logger.error('GCS copy failed', error, { sourceObjectName, destObjectName });
      throw error;
    }
  }
}

/**
 * Cloud Backup Factory
 * Creates appropriate cloud backup service based on provider
 */
export class CloudBackupFactory {
  static create(provider: CloudProvider, config: CloudStorageConfig): CloudBackupService {
    switch (provider) {
      case CloudProvider.AWS_S3:
        return new S3BackupService(config as S3Config);

      case CloudProvider.AZURE_BLOB:
        return new AzureBlobBackupService(config as AzureBlobConfig);

      case CloudProvider.GOOGLE_CLOUD:
        return new GcsBackupService(config as GcsConfig);

      case CloudProvider.LOCAL:
        throw new Error('Local storage provider should use file system operations directly');

      default:
        throw new Error(`Unsupported cloud provider: ${provider}`);
    }
  }

  static isProviderAvailable(provider: CloudProvider): boolean {
    try {
      switch (provider) {
        case CloudProvider.AWS_S3:
          require.resolve('@aws-sdk/client-s3');
          return true;

        case CloudProvider.AZURE_BLOB:
          require.resolve('@azure/storage-blob');
          return true;

        case CloudProvider.GOOGLE_CLOUD:
          require.resolve('@google-cloud/storage');
          return true;

        default:
          return false;
      }
    } catch (error) {
      return false;
    }
  }
}

export default CloudBackupService;
