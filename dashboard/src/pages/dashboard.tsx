import React, { useState, useEffect } from 'react';
import {type Collection} from '~/types/collectionTypes';
import {type Binding} from '~/types/bindingTypes';
import {type Index} from '~/types/indexTypes';
import DashboardComponent from '~/components/DashboardComponent';
import { fetchCollections, fetchBindings, fetchIndexes } from "~/api/apiService";

const Dashboard: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [bindings, setBindings] = useState<Binding[]>([]);
  const [indexes, setIndexes] = useState<Index[]>([]);

  useEffect(() => {

    const getCollections = async () => {
        try {
          const data = await fetchCollections();
          setCollections(data);
        } catch (error) {
          console.error('Error fetching collections:', error);
        }
    };

    const getBindings = async () => {
        // Fetch bindings from the API and update state
      try {
        const data = await fetchBindings();
        setBindings(data);
      } catch (error) {
        console.error('Error fetching bindings:', error);
      }
    };

    const getIndexes = async () => {
        // Fetch indexes from the API and update state
      try {
        const data = await fetchIndexes();
        setIndexes(data);
      } catch (error) {
        console.error('Error fetching indexes:', error);
      }
    };

    void getCollections();
    void getBindings();
    void getIndexes();
  }, []);

  return (
    <div className="App">
      <DashboardComponent
        collections={collections}
        bindings={bindings}
        indexes={indexes}
      />
    </div>
  );
};

export default Dashboard;
