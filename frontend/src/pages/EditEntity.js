import React, {useEffect, useState} from "react";
import {makeStyles} from "@material-ui/core/styles";
import {Table, TableBody, TableCell, TableFooter, TableHead, TableRow} from "@material-ui/core";

const useStyles = makeStyles((theme) => ({
    button: {
        margin: theme.spacing(1),
    },
}));

// TODO implement it
export default function EditEntity(props) {
    const classes = useStyles();
    const [entity, setEntity] = useState({attributes: []});

    useEffect(() => {
        setEntity({
            id: 1,
            name: 'entity1',
            attributes: [
                {
                    id: 1,
                    name: "attr1",
                },
                {
                    id: 2,
                    name: "attr2",
                },
            ]
        })
    }, []);

    const onSubmit = (event) => {
        console.log(event);
        event.preventDefault();
    };

    return (
        <form onSubmit={onSubmit}>
            <div className="container-fluid">
                <div className="row">
                    <div className="col">
                        <div className="float-right">
                            <input name="button_save" type="submit" className="btn btn-primary" value='保存'></input>
                        </div>
                        <table className="table table-bordered">
                            <tr>
                                <td>エンティティ名</td>
                                <td><input type="text" name="name" value={entity.name}/></td>
                            </tr>
                            <tr>
                                <td>備考</td>
                                <td><input type="text" name="note" size="50" value={entity.note}/></td>
                            </tr>
                            <tr>
                                <td>サイドバーに表示</td>
                                <td><input type="checkbox" name="is_toplevel"/></td>
                            </tr>
                        </table>

                        <Table className="table table-bordered">
                            <TableHead>
                                <TableRow>
                                    <TableCell>属性名</TableCell>
                                    <TableCell>型</TableCell>
                                    <TableCell>オプション</TableCell>
                                    <TableCell/>
                                </TableRow>
                            </TableHead>

                            <TableBody id='sortdata'>
                                {
                                    entity.attributes.map((attr) => {
                                        return (
                                            <TableRow className="attr">
                                                <input type='hidden' className="row_index" value={0}/>
                                                <TableCell><input type="text" className="attr_name" value={attr.name}/></TableCell>
                                                <TableCell>
                                                    <div className='row'>
                                                        型選択あとでやる
                                                    </div>
                                                </TableCell>

                                                <TableCell>
                                                <span className='attr_option_mandatory' data-toggle="tooltip">
                                                    <input type="checkbox" className="is_mandatory"/> 必須
                                                </span>

                                                    <br/>

                                                    <span className='attr_option_delete_in_chain' data-toggle="tooltip">
                                                <input type="checkbox" className="is_delete_in_chain"/> 関連削除
                                            </span>
                                                </TableCell>

                                                <TableCell>
                                                    <a href={`/acl/${attr.id}`}>
                                                        <button type="button" className="btn btn-info btn-sm">ACL
                                                        </button>
                                                    </a>
                                                    <button type="button" className="btn btn-danger btn-sm"
                                                            name="del_attr">delete
                                                    </button>
                                                </TableCell>
                                            </TableRow>)
                                    })
                                }
                            </TableBody>

                            <TableFooter>
                                <TableRow>
                                    <TableCell><input type="text" className="attr_name"></input></TableCell>
                                    <TableCell>

                                        <div className='row'>
                                            <div className='col-4'>
                                                型選択あとでやる
                                            </div>
                                            <div className='col-8'>

                                                <ul className='list-group'>
                                                </ul>

                                                <select className="attr_referral template" size="3" multiple="True">
                                                </select>

                                                <input type="text" className="narrow_down_referral" placeholder="絞り込み"/>

                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                    <span className='attr_option_mandatory' data-toggle="tooltip">
                                    <input type="checkbox" className="is_mandatory"/> 必須
                                    </span>

                                        <br/>

                                        <span className='attr_option_delete_in_chain' data-toggle="tooltip">
                                    <input type="checkbox" className="is_delete_in_chain"/> 関連削除
                                    </span>
                                    </TableCell>
                                    <TableCell>
                                        <button type="button" className="btn btn-danger btn-sm" name="del_attr">del
                                        </button>
                                    </TableCell>
                                    <input type='hidden' className="row_index"/>
                                </TableRow>
                            </TableFooter>
                        </Table>
                    </div>
                </div>

                <div className="row">
                    <div className="col">
                        <button type="button" className="btn btn-primary" name="add_attr">属性追加</button>
                    </div>
                </div>
            </div>
        </form>
    );
}