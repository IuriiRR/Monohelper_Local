import { useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  NumberInput,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useSyncAccounts, useSyncTransactions, useTasks } from '../hooks/useSync'

const STATUS_COLORS: Record<string, string> = {
  success: 'green',
  error: 'red',
  running: 'blue',
  pending: 'gray',
}

function formatIso(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : '—'
}

export function Sync() {
  const [days, setDays] = useState(30)
  const tasks = useTasks()
  const syncAccounts = useSyncAccounts()
  const syncTransactions = useSyncTransactions()

  return (
    <Stack>
      <Title order={2}>Sync</Title>

      <Group align="flex-end">
        <Button onClick={() => syncAccounts.mutate()} loading={syncAccounts.isPending}>
          Sync accounts
        </Button>
        <NumberInput
          label="Days"
          value={days}
          onChange={(v) => setDays(typeof v === 'number' ? v : 30)}
          min={1}
          max={90}
          maw={120}
        />
        <Button
          variant="light"
          onClick={() => syncTransactions.mutate(days)}
          loading={syncTransactions.isPending}
        >
          Sync transactions
        </Button>
      </Group>

      {(syncAccounts.isError || syncTransactions.isError) && (
        <Alert color="red">
          {(syncAccounts.error as Error)?.message ?? (syncTransactions.error as Error)?.message}
        </Alert>
      )}

      <Card withBorder>
        <Title order={4} mb="sm">
          Recent tasks
        </Title>
        {tasks.isLoading ? (
          <Text c="dimmed">Loading…</Text>
        ) : (
          <Table.ScrollContainer minWidth={640}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>ID</Table.Th>
                  <Table.Th>Type</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Attempts</Table.Th>
                  <Table.Th>Created</Table.Th>
                  <Table.Th>Finished</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {(tasks.data?.tasks ?? []).map((t) => (
                  <Table.Tr key={t.id}>
                    <Table.Td>{t.id}</Table.Td>
                    <Table.Td>{t.type}</Table.Td>
                    <Table.Td>
                      <Badge color={STATUS_COLORS[t.status] ?? 'gray'}>{t.status}</Badge>
                    </Table.Td>
                    <Table.Td>{t.attempts}</Table.Td>
                    <Table.Td>{formatIso(t.created_at)}</Table.Td>
                    <Table.Td>{formatIso(t.finished_at)}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </Card>
    </Stack>
  )
}
