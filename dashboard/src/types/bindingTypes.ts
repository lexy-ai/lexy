import { type Collection } from './collectionTypes';
import { type Index } from './indexTypes';
import { type Filter } from './filterTypes';
import { type Transformer } from './transformerTypes';

export interface TransformerParams {
  lexy_index_fields?: (string)[] | null;
}

export interface Binding {
  collection_id: string;
  transformer_id: string;
  index_id: string;
  description: string | null;
  execution_params: never;
  transformer_params: TransformerParams;
  filter: Filter | null;
  binding_id: number;
  created_at: string;
  updated_at: string;
  status: string;
  collection: Collection;
  transformer: Transformer;
  index: Index;
}