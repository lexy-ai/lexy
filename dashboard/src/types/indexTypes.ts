export interface IndexFieldDetail {
  type: string;
  optional?: boolean;
  extras?: {
    dims?: number;
    model?: string;
  };
}

export type IndexFields = Record<string, IndexFieldDetail>;

export interface Index {
  index_id: string;
  description: string;
  index_table_schema: object; // Add more specific type if you have the schema structure
  index_fields: IndexFields;
  created_at: string;
  updated_at: string;
  index_table_name: string;
}
