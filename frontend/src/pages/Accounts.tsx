import { Alert, Badge, Loader, Stack, Table, Title } from '@mantine/core'
import { useAccounts } from '../hooks/useAccounts'
import { formatCurrency } from '../lib/format'

export function Accounts() {
  const { data, isLoading, error } = useAccounts()

  return (
    <Stack>
      <Title order={2}>Accounts</Title>
      {isLoading && <Loader />}
      {error && <Alert color="red">{(error as Error).message}</Alert>}

      {!isLoading && !error && (
        <Table.ScrollContainer minWidth={640}>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Title</Table.Th>
                <Table.Th>Type</Table.Th>
                <Table.Th>Balance</Table.Th>
                <Table.Th>Budget</Table.Th>
                <Table.Th>Active</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(data?.accounts ?? []).map((a) => (
                <Table.Tr key={a.id}>
                  <Table.Td>{a.title ?? a.id}</Table.Td>
                  <Table.Td>{a.type}</Table.Td>
                  <Table.Td>{formatCurrency(a.balance)}</Table.Td>
                  <Table.Td>{a.is_budget ? <Badge>Budget</Badge> : null}</Table.Td>
                  <Table.Td>{a.is_active ? 'Yes' : 'No'}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}
    </Stack>
  )
}
