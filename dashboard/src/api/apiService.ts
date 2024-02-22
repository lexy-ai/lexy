import {type Collection} from '~/types/collectionTypes';
import {type Binding} from '~/types/bindingTypes';
import {type Index} from '~/types/indexTypes';

// Define a base URL for your API if it's different from the root
const API_BASE_URL = 'http://localhost:9900';

// Function to fetch collections from the backend
export const fetchCollections = async (): Promise<Collection[]> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/collections`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json() as Collection[];
    } catch (error) {
        console.error('There was a problem fetching collections:', error);
        throw error;
    }
};

// Function to fetch bindings from the backend
export const fetchBindings = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/bindings`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json() as Binding[];
    } catch (error) {
        console.error('There was a problem fetching bindings:', error);
        throw error;
    }
};

// Function to fetch indexes from the backend
export const fetchIndexes = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/indexes`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json() as Index[];
    } catch (error) {
        console.error('There was a problem fetching indexes:', error);
        throw error;
    }
};
