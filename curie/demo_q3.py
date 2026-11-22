"""Wave 3 microscope demonstration."""
import json
from .trace import tracing, explain
from .verify import verify
from .diff import diff
from .programs import grover_circuit, run
from .qstate import zeros


def main():
    with tracing() as trace:
        trace.run(grover_circuit(2, 3, 1), zeros(2))
    data = json.loads(trace.to_json())
    print(explain(data))
    print('VERIFIED' if verify(data).ok else 'VERIFICATION FAILED')
    data['steps'][2]['after'][0][0] += 0.1
    result = verify(data)
    print(f"MISMATCH at step {result.step} ({data['steps'][result.step]['op']})")
    initial, _ = run([('h', (0,)), ('h', (1,))], zeros(2))
    cz = [('cz', (0, 1))]
    correct = [('h', (1,)), ('cnot', (0, 1)), ('h', (1,))]
    wrong = [('h', (1,)), ('cnot', (0, 1)), ('h', (0,))]
    print('CZ vs H-CNOT-H: ' + ('EQUIVALENT' if diff(cz, correct, initial, [('end', 1, 3)]).equivalent else 'DIFFERENT'))
    result = diff(correct, wrong, zeros(2))
    print(f'DIVERGES at index {result.where}' if not result.equivalent else 'EQUIVALENT')


if __name__ == '__main__':
    main()
