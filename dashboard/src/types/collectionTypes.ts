export interface CollectionConfig {
  store_files?: boolean;
  generate_thumbnails?: boolean;
}

export interface Collection {
  collection_id: string;
  collection_name: string;
  description: string | null;
  config: CollectionConfig;
  created_at: string;
  updated_at: string;
}
