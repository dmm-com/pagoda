import React from 'react';
import { shallow } from 'enzyme';

import { JobList } from './JobList';

it('fuga', () => {
  console.log('[onix-test/fuga.JobList(00)]');

  const wrapper = shallow(<JobList jobs={[]} />);
  console.log('[onix-test/fuga.JobList(10)] wrapper');
  console.log(wrapper)
});

