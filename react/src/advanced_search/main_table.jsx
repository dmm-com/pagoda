import $ from 'jquery';
import React from 'react';
import {Entry} from './entry';

export class MainTable extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            results: [],
        };
    }

    componentDidMount() {
        this.fetch(this);
    }

    fetch(that) {
        const request_params = {
            entities: this.props.entities,
            entry_name: $('.hint_entry_name').val(),
            attrinfo: this.get_attrinfo(),
        };

        if($('#check_search_all').is(':checked')) {
            request_params['entry_limit'] = 99999;
        }

        $.ajax({
            type: 'POST',
            url: "/api/v1/entry/search",
            data: JSON.stringify(request_params),
            dataType:      'json',
            contentType:   'application/json;charset=utf-8',
            scriptCharset: 'utf-8',
            headers: {
                'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
            },
        }).done(function(data){
            that.setState({
                results: data.result.ret_values,
            });
        }).fail(function(data){
            MessageBox.error(data.responseText);
        });
    }

    get_attrinfo() {
        return $('.hint_attr_value').map(function() {
            return {
                'name': $(this).attr('attrname'),
                'keyword': $(this).val(),
            }
        }).get();
    }

    render() {
        return (
            this.state.results.map((r) =>
                <Entry entry={r.entry} entity={r.entity} attrs={r.attrs}/>
            )
        );
    }
}