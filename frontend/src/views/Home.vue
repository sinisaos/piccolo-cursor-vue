<template>
    <div class="container">
        <div
            :key="index"
            class="col-md-8 offset-md-2"
            v-for="(item, index) in tasks"
        >
            <h4>
                <b>{{ item.id }} - {{ item.name }}</b>
            </h4>
            <p class="mb-1">{{ item.completed }}</p>
            <hr />
        </div>
        <div class="col-md-8 offset-md-2">
            <button
                @click="getPrevTasks"
                class="btn btn-info"
                style="display: none"
                v-if="tasks[0]['id'] == firstRow"
            >
                Previous
            </button>
            <button @click="getPrevTasks" class="btn btn-info" v-else>
                Previous
            </button>
            &nbsp;
            <button
                @click="getTasks"
                class="btn btn-info"
                v-if="tasks[tasks.length - 1]['id'] != lastRow"
            >
                Next
            </button>
        </div>
        <br />
    </div>
</template>

<script>
import axios from "axios"

export default {
    data() {
        return {
            tasks: [],
            cursor: "",
            firstRow: "",
            lastRow: ""
        }
    },
    methods: {
        getTasks() {
            const path = "/tasks/?__cursor=" + this.cursor
            axios
                .get(path)
                .then((res) => {
                    this.tasks = res.data.rows
                    this.cursor = res.headers["next_cursor"]
                    this.firstRow = parseInt(res.headers["first_row"])
                    this.lastRow = parseInt(res.headers["last_row"])
                })
                .catch((error) => {
                    // eslint-disable-next-line
                    console.error(error)
                })
        },
        getPrevTasks() {
            const path = "/tasks/?__cursor=" + this.cursor + "&__previous=yes"
            axios
                .get(path)
                .then((res) => {
                    this.tasks = res.data.rows
                    this.cursor = res.headers["next_cursor"]
                    this.previous = res.headers["no_results"]
                })
                .catch((error) => {
                    // eslint-disable-next-line
                    console.error(error)
                })
        }
    },
    created() {
        this.getTasks()
    }
}
</script>

<style scoped>
.container {
    padding: 3rem;
}
</style>
