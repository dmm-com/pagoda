import React from 'react';
import { useParams, Link } from "react-router-dom";
import { shallow } from 'enzyme';

import { EditEntry } from './EditEntry';

beforeAll(() => {
  console.log('[onix-test/beforeAll(00)]');

  jest.mock("react-router-dom", () => {
    useParams: jest.fn(() => {
      console.log('[onix-test/(Mock)useParams(00)]');

      return {
        entityId: 100,
        entryId: 10,
      };
    })
  });
});

it('hoge', () => {
  console.log('[onix-test/fuga.EditEntry(00)]');

  const wrapper = shallow(<EditEntry entityId={1} entryId={1} />);
  console.log('[onix-test/hoge.EditEntry(10)] wrapper');
  console.log(wrapper)
});

/*
it('fuga', () => {
  console.log('[onix-test/fuga.EditEntry(00)]');

  const useParams = jest.fn(() => {
    return {'entityId': 'hoge', 'entryId': 'fuga', 'foo': 'puyo'};
  });

  const { entityId, entryId } = useParams();
  //const entityId = useParams();
  console.log(`[onix-test/fuga.EditEntry(10)] entityId: ${entityId}`);
});
*/
