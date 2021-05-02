import React from 'react';

export class Entry extends React.Component {
    render() {
        return (
            <tr>
                <th>
                    <a href={"/entry/show/" + this.props.entry.id + "/"}>{this.props.entry.name} [{this.props.entity.name}]</a>
                </th>
                {
                    Object.entries(this.props.attrs).map(([name, attr]) =>
                        <td>
                            {attr.value}
                        </td>
                    )
                }
            </tr>
        );
    }

}