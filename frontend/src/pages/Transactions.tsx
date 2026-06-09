import { useState } from 'react'
import { Alert, Loader, Select, Stack, Table, Title } from '@mantine/core'
import { useAccounts } from '../hooks/useAccounts'
import { useTransactions } from '../hooks/useTransactions'
import { formatCurrency, formatDateTime } from '../lib/format'

export function Transactions() {
  const [accountId, setAccountId] = useState<string | null>(null)
  const accounts = useAccounts()
  const { data, isLoading, error } = useTransactions(accountId ?? undefined)

  return (
    <Stack>
      <Title order={2}>Transactions</Title>
      <Select
        label="Account"
        placeholder="All accounts"
        clearable
        data={(accounts.data?.accounts ?? []).map((a) => ({ value: a.id, label: a.title ?? a.id }))}
        value={accountId}
        onChange={setAccountId}
        maw={320}
      />

      {isLoading && <Loader />}
      {error && <Alert color="red">{(error as Error).message}</Alert>}

      {!isLoading && !error && (
        <Table.ScrollContainer minWidth={700}>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Time</Table.Th>
                <Table.Th>Description</Table.Th>
                <Table.Th>Amount</Table.Th>
                <Table.Th>Balance</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(data?.transactions ?? []).map((t) => (
                <Table.Tr key={t.id}>
                  <Table.Td>{formatDateTime(t.time)}</Table.Td>
                  <Table.Td>{t.comment || t.description || '—'}</Table.Td>
                  <Table.Td c={t.amount < 0 ? 'red' : 'green'}>{formatCurrency(t.amount)}</Table.Td>
                  <Table.Td>{formatCurrency(t.balance)}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}
    </Stack>
  )
}
