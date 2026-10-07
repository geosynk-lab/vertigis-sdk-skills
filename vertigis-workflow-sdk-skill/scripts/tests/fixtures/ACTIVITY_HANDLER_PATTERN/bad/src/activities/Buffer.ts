import type { IActivityHandler } from "@vertigis/workflow";

type Units = "meters" | "feet";
interface BufferInputs { units?: Units; distance: number }
interface BufferOutputs { result: number }

export default class BufferActivity {
    execute(inputs: BufferInputs): BufferOutputs {
        return { result: inputs.distance };
    }
}
