// Define the Value type which can be a single value or an array of values.
export type FilterValue = string | number | boolean | (string | number | boolean)[] | null;

// Define the Condition interface.
export interface FilterCondition {
  field: string;
  operation: string;
  value: FilterValue;
  negate: boolean;
}

// Define the Filter interface.
export interface Filter {
  conditions: FilterCondition[];
  combination: string;
}
