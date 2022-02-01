import { EntryList as EntryListOirg } from "../../pages/EntryList"

export const EntryList: FC = () => {
  const classes = useStyles();
  const { entityId } = useParams<{ entityId: number }>();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>();

  const entity = useAsync(async () => {
    const resp = await getEntity(entityId);
    return await resp.json();
  });

  const entries = useAsync(async () => {
    const resp = await getEntries(entityId, true);
    const data = await resp.json();
    return data.results;
  });

  if (entity.name == '(Network)') {
    return (
      <NetworkEntryList entityId={ entityId } />
    );
  } else {
    return (
      <EntryListOirg entityId={ entityId } />
    );
  }
};
